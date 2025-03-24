import datetime
import json
class CustomTimestampReranker:
    def __init__(self, verbose=False, top_n=3):
        self.verbose = verbose
        self.top_n = top_n

    def debug_print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def extract_timestamp(self, node):
        """
        Extracts the timestamp from the node's metadata.
        It first attempts to read the 'window' field (expected as a JSON string),
        then falls back to the direct 'timestamp' field if needed.
        Returns a float (epoch seconds) for sorting; otherwise returns 0.
        """
        metadata = node.node.metadata if hasattr(node, "node") else node.metadata
        self.debug_print("Node metadata:", metadata)
        ts = None

        # Attempt to extract from the "window" field
        window_str = metadata.get("window", "")
        if window_str:
            try:
                self.debug_print("Found window field:", window_str)
                window_obj = json.loads(window_str)
                ts = window_obj.get("timestamp", None)
                self.debug_print("Extracted timestamp from window:", ts)
            except json.JSONDecodeError as e:
                self.debug_print("Window field is not valid JSON:", window_str, "Error:", e)
        else:
            self.debug_print("No window field found.")

        # Fall back to direct 'timestamp' field if not found in window
        if not ts:
            ts = metadata.get("timestamp", None)
            self.debug_print("Falling back to direct timestamp:", ts)

        if ts is None or ts == "":
            self.debug_print("No valid timestamp found; defaulting to 0.")
            return 0

        # Try converting directly to float (in case it's already numeric)
        try:
            ts_float = float(ts)
            self.debug_print("Timestamp as float:", ts_float)
            return ts_float
        except Exception as e:
            self.debug_print("Could not convert timestamp to float directly, trying ISO parsing. Error:", e)

        # Attempt to parse ISO 8601 timestamp
        try:
            if ts.endswith("Z"):
                ts = ts[:-1]
            try:
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
            ts_float = dt.timestamp()
            self.debug_print("Parsed ISO timestamp as float:", ts_float)
            return ts_float
        except Exception as e:
            self.debug_print("Could not parse timestamp as ISO date, using 0. Error:", e)
            return 0

    def postprocess_nodes(self, nodes, query_bundle=None):
        """
        Sorts the nodes from newest to oldest based on the extracted timestamp,
        and then returns up to `top_n` unique nodes (deduplicated by 'email_id').
        """
        # Determine the list of nodes to work with
        if hasattr(nodes, "source_nodes"):
            self.debug_print("CustomTimestampReranker received source_nodes:")
            node_list = nodes.source_nodes
        else:
            self.debug_print("CustomTimestampReranker received nodes list:")
            node_list = nodes

        # Sort nodes in descending order based on timestamp
        sorted_nodes = sorted(
            node_list,
            key=lambda node: self.extract_timestamp(node),
            reverse=True
        )
        self.debug_print("After sorting, nodes are:")
        for node in sorted_nodes:
            self.debug_print("Node text:", node.node.text if hasattr(node, "node") else node.text,
                             "Extracted timestamp:", self.extract_timestamp(node))

        # Deduplicate nodes based on 'email_id' and take the top_n
        unique_nodes = []
        seen_ids = set()
        for node in sorted_nodes:
            email_id = (node.node.metadata if hasattr(node, "node") else node.metadata).get("email_id")
            if email_id not in seen_ids:
                unique_nodes.append(node)
                seen_ids.add(email_id)
            if len(unique_nodes) == self.top_n:
                break

        self.debug_print("Unique nodes selected (top_n={}):".format(self.top_n))
        for node in unique_nodes:
            self.debug_print("Node text:", node.node.text if hasattr(node, "node") else node.text,
                             "Email ID:", (node.node.metadata if hasattr(node, "node") else node.metadata).get("email_id"),
                             "Extracted timestamp:", self.extract_timestamp(node))
            
        # Assign back to the appropriate attribute if needed
        if hasattr(nodes, "source_nodes"):
            nodes.source_nodes = unique_nodes
            return nodes
        else:
            return unique_nodes