"use client";

import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    IconButton,
    TextField,
    Button,
    Typography,
    Paper,
    createTheme,
    ThemeProvider,
    CssBaseline,
    CircularProgress,
} from '@mui/material';
import { ThumbUp, ThumbDown, Add, Delete, Send as SendIcon } from '@mui/icons-material';


interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
    rating?: 'up' | 'down';
}

interface Conversation {
    id: number;
    title: string;
    messages: Message[];
}


const drawerWidth = 280;
const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: { main: '#84EEF2' },
        background: { default: '#00033A', paper: '#0A0D4B' },
        text: { primary: '#CED6E8', secondary: '#A8B2D1' },
        success: { main: '#4CAF50' },
        error: { main: '#F44336' },
        action: { disabledBackground: 'rgba(124, 115, 255, 0.2)', disabled: 'rgba(255, 255, 255, 0.3)' },
        secondary: { main: '#ff6b6b' } 
    },
    typography: {
        fontFamily: 'var(--font-jetbrains-mono), monospace',
        button: { textTransform: 'none' },
        h5: {
            fontWeight: 700,
            fontSize: '1.7rem',
            color: '#84EEF2',
            textAlign: 'center',
        },
        body1: {
            fontSize: '1rem',
            lineHeight: 1.6,
        },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    backgroundColor: 'transparent',
                    boxShadow: 'none',
                },
            },
        },
        MuiIconButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                },
            },
        },
        MuiOutlinedInput: {
            styleOverrides: {
                root: {
                    fontFamily: 'var(--font-jetbrains-mono), monospace',
                    fontSize: 16,
                    borderRadius: '8px',
                    '& fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: '1px',
                    },
                    '&:hover fieldset': {
                        borderColor: 'rgba(132, 238, 242, 0.7)',
                    },
                    '&.Mui-focused fieldset': {
                        borderColor: '#84EEF2',
                        borderWidth: '1px',
                    },
                },
                input: {
                    color: '#CED6E8',
                    padding: '12px 14px',
                    '&::placeholder': {
                        color: '#7A849D',
                        opacity: 1,
                    },
                },
            },
        },
        MuiListItemButton: {
            styleOverrides: {
                root: {
                    borderRadius: '4px',
                    paddingRight: '4px',
                    '&.Mui-selected': {
                        backgroundColor: 'rgba(132, 238, 242, 0.15)',
                        '&:hover': {
                            backgroundColor: 'rgba(132, 238, 242, 0.25)',
                        },
                    },
                    '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                },
            },
        },
    },
});


const ChatUI: React.FC = () => {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConvId, setCurrentConvId] = useState<number | null>(null);
    const [newMessage, setNewMessage] = useState('');
    const [isBotLoading, setIsBotLoading] = useState(false);
    const [isFetchingMessages, setIsFetchingMessages] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const currentConversation = conversations.find((c) => c.id === currentConvId);

    const generateChatTimestamp = (): string => {
        const date = new Date();
        const pad = (num: number) => String(num).padStart(2, '0');
        const day = pad(date.getDate());
        const month = pad(date.getMonth() + 1);
        const year = date.getFullYear();
        const hours = pad(date.getHours());
        const minutes = pad(date.getMinutes());
        return `Chat ${day}.${month}.${year} ${hours}:${minutes}`;
    };


    const fetchMessagesForConversation = async (conversationId: number): Promise<Message[]> => {
        try {
            const msgRes = await fetch(
                `http://localhost:8000/api/messages/?conversation=${conversationId}`
            );
            if (!msgRes.ok) {
                console.error("Failed to fetch messages:", msgRes.status, await msgRes.text());
                return [];
            }
            const messagesData = await msgRes.json();

            const mappedMessages = messagesData.map((msg: any) => {
                const apiRating = msg.rating; // Expects "up", "down", null

                const frontendRating = apiRating === 'up' ? 'up' : apiRating === 'down' ? 'down' : undefined;

                return {
                    id: msg.id,
                    text: msg.text,
                    sender: msg.sender,
                    rating: frontendRating, 
                };
            });

            return mappedMessages;

        } catch (error) {
            console.error('Error fetching messages:', error);
            return [];
        }
    };

    const fetchConversations = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/conversations/');
            if (!res.ok) {
                console.error("Failed to fetch conversations:", res.status, await res.text());
                throw new Error('Failed to fetch conversations');
            }
            const data = await res.json();

            const sortedData = data.sort((a: {id: number}, b: {id: number}) => b.id - a.id);

            const formatted: Conversation[] = sortedData.map((conv: any) => ({
                id: conv.id,
                title: conv.title || `Chat ${conv.id}`,
                messages: [], 
            }));

            setConversations(formatted);

            if (formatted.length > 0 && currentConvId === null) {
                const currentConvExists = formatted.some(conv => conv.id === currentConvId);
                if (currentConvId !== null && currentConvExists) {
                    const conv = formatted.find(c => c.id === currentConvId);
                    if (conv && conv.messages.length === 0) {
                        handleSelectConversation(currentConvId); 
                    }
                }
                else if (currentConvId === null || !currentConvExists) {
                     handleSelectConversation(formatted[0].id);
                }
            }
            else if (formatted.length === 0) {
                setCurrentConvId(null);
            }

        } catch (err) {
            console.error('Failed to fetch conversations:', err);
        }
    };

    const handleSelectConversation = async (conversationId: number) => {
        if (conversationId === currentConvId && currentConversation?.messages.length > 0) {
           return;
        }
        setCurrentConvId(conversationId);
        setIsFetchingMessages(true);
        try {
            const messages = await fetchMessagesForConversation(conversationId);
            setConversations((prevConvs) =>
                prevConvs.map((conv) =>
                    conv.id === conversationId ? { ...conv, messages } : conv
                )
            );
        } catch (error) {
            console.error(`Error loading messages for conversation ${conversationId}:`, error);
        } finally {
            setIsFetchingMessages(false);
        }
    };

    useEffect(() => {
        fetchConversations();
    }, []);

    useEffect(() => {
         if (currentConversation?.messages && currentConversation.messages.length > 0 && !isBotLoading && !isFetchingMessages) {
            const timer = setTimeout(() => {
                messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
            }, 100);
             return () => clearTimeout(timer);
        }
    }, [currentConversation?.messages, isBotLoading, isFetchingMessages]);


    const handleSend = async () => {
        if (!newMessage.trim() || currentConvId === null) return;
        const textToSend = newMessage;
        setNewMessage('');

        const optimisticUserMessage: Message = {
            id: Date.now(),
            text: textToSend,
            sender: 'user',
        };

        setConversations((prevConvs) =>
            prevConvs.map((conv) =>
                conv.id === currentConvId
                    ? { ...conv, messages: [...conv.messages, optimisticUserMessage] }
                    : conv
            )
        );
        setIsBotLoading(true);

        try {
            const sendRes = await fetch('http://localhost:8000/api/messages/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation: currentConvId,
                    sender: 'user',
                    text: textToSend,
                }),
            });

            if (!sendRes.ok) {
                const errorText = await sendRes.text();
                console.error('Failed to send message:', sendRes.status, errorText);
                throw new Error(errorText || 'Failed to send message');
            }

            const updatedMessages = await fetchMessagesForConversation(currentConvId);
            setConversations((prevConvs) =>
                prevConvs.map((conv) =>
                    conv.id === currentConvId ? { ...conv, messages: updatedMessages } : conv
                )
            );

        } catch (error) {
            console.error('Error sending message or fetching reply:', error);
            setConversations((prevConvs) =>
                prevConvs.map((conv) =>
                    conv.id === currentConvId
                        ? {
                            ...conv,
                            messages: conv.messages.filter(
                                (msg) => msg.id !== optimisticUserMessage.id
                            ),
                        }
                        : conv
                )
            );
            setNewMessage(textToSend);
        } finally {
            setIsBotLoading(false);
        }
    };

    const handleNewConversation = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/conversations/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: generateChatTimestamp(), user: 1 }),
            });

            if (!res.ok) {
                const errorText = await res.text();
                console.error('Failed to create conversation:', res.status, errorText);
                throw new Error(errorText || 'Failed to create conversation');
            }
            const newConvData = await res.json();

            const newConv: Conversation = {
                id: newConvData.id,
                title: newConvData.title || `Chat ${newConvData.id}`,
                messages: [],
            };
            setConversations((prev) => [newConv, ...prev]);
            setCurrentConvId(newConv.id);
            setIsFetchingMessages(false);
            setIsBotLoading(false);
            setNewMessage('');
        } catch (error) {
            console.error('Error creating new conversation:', error);
        }
    };

    const handleDeleteConversation = async (idToDelete: number) => {

        try {
            const res = await fetch(`http://localhost:8000/api/conversations/${idToDelete}/`, {
                method: 'DELETE',
                headers: {
                },
            });

            if (!res.ok) {
                 const errorText = await res.text();
                 console.error(`Failed to delete conversation ${idToDelete}:`, res.status, errorText);
                 throw new Error(errorText || 'Failed to delete conversation');
            }

            setConversations(prev => prev.filter(conv => conv.id !== idToDelete));

            if (currentConvId === idToDelete) {
                setCurrentConvId(null);
            }

        } catch (error) {
            console.error('Error deleting conversation:', error);
            alert(`Error deleting conversation: ${error}`);
        }
    };


     const handleRatingOld = async (messageId: number, newRating: 'up' | 'down') => {
        if (currentConvId === null) return;

        const conversationIndex = conversations.findIndex(c => c.id === currentConvId);
        if (conversationIndex === -1) return;
        const messageIndex = conversations[conversationIndex].messages.findIndex(m => m.id === messageId);
        if (messageIndex === -1) return;

        const currentMessage = conversations[conversationIndex].messages[messageIndex];
        const previousRating = currentMessage.rating;

        if (previousRating === newRating) return; 

        const updatedConversations = conversations.map((conv, index) => {
            if (index === conversationIndex) {
                const updatedMessages = conv.messages.map((msg, msgIdx) => {
                    if (msgIdx === messageIndex) {
                        return { ...msg, rating: newRating };
                    }
                    return msg;
                });
                return { ...conv, messages: updatedMessages };
            }
            return conv;
        });
        setConversations(updatedConversations);

        try {
            const ratingValueToSend = newRating;

            const res = await fetch('http://localhost:8000/api/ratings/', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: messageId,
                    value: ratingValueToSend
                 }),
            });

            if (!res.ok) {
                const errorText = await res.text();
                console.error('Failed to send rating:', res.status, errorText);
                throw new Error(errorText || 'Failed to send rating');
            }


        } catch (err) {
            console.error('Error sending rating:', err);
             const revertedConversations = conversations.map((conv, index) => {
                 if (index === conversationIndex) {
                     const revertedMessages = conv.messages.map((msg, msgIdx) => {
                         if (msg.id === messageId) {
                             return { ...msg, rating: previousRating };
                         }
                         return msg;
                     });
                     return { ...conv, messages: revertedMessages };
                 }
                 return conv;
             });
            setConversations(revertedConversations);
        }
    };

    
    const handleRating = async (messageId: number, clickedRating: 'up' | 'down') => {
        if (currentConvId === null) return;

        let previousRating: 'up' | 'down' | undefined = undefined;
        let targetConversationIndex = -1;
        let targetMessageIndex = -1;

        targetConversationIndex = conversations.findIndex(c => c.id === currentConvId);
        if (targetConversationIndex === -1) return;

        targetMessageIndex = conversations[targetConversationIndex].messages.findIndex(m => m.id === messageId);
        if (targetMessageIndex === -1) return;

        previousRating = conversations[targetConversationIndex].messages[targetMessageIndex].rating;

        const nextRatingForState: 'up' | 'down' | undefined =
            previousRating === clickedRating ? undefined : clickedRating;

        setConversations(prevConvs =>
            prevConvs.map((conv, convIndex) => {
                if (convIndex === targetConversationIndex) {
                    const updatedMessages = conv.messages.map((msg, msgIndex) => {
                        if (msgIndex === targetMessageIndex) {
                            return { ...msg, rating: nextRatingForState };
                        }
                        return msg;
                    });
                    return { ...conv, messages: updatedMessages };
                }
                return conv;
            })
        );

        try {
            let ratingValueToSend: number | null;
            if (nextRatingForState === 'up') {
                ratingValueToSend = 1;
            } else if (nextRatingForState === 'down') {
                ratingValueToSend = -1;
            } else {
                ratingValueToSend = null;
            }


            const res = await fetch('http://localhost:8000/api/ratings/', {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: messageId,
                    value: ratingValueToSend
                 }),
            });


            if (!res.ok) {
                const errorText = await res.text();
                console.error('Failed to send rating:', res.status, errorText);
                throw new Error(errorText || 'Failed to send rating');
            }


        } catch (err) {
            console.error('Error sending rating:', err);

            setConversations(prevConvs =>
                prevConvs.map((conv, convIndex) => {
                    if (convIndex === targetConversationIndex) {
                        const revertedMessages = conv.messages.map((msg, msgIndex) => {
                            if (msgIndex === targetMessageIndex) {
                                return { ...msg, rating: previousRating };
                            }
                            return msg;
                        });
                        return { ...conv, messages: revertedMessages };
                    }
                    return conv;
                })
             );
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        setNewMessage(suggestion);
    };

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box
                sx={{
                    display: 'flex',
                    height: '100vh',
                    width: '100vw',
                    bgcolor: 'background.default',
                    position: 'relative',
                    overflow: 'hidden',
                }}
            >
                 <Box
                    sx={{
                        width: { xs: 200, md: 280 },
                        height: { xs: 200, md: 280 },
                        left: '55%',
                        top: '60%',
                        transform: 'translate(-50%, -50%)',
                        position: 'absolute',
                        background: '#6D2FFF',
                        boxShadow: '300px 300px 300px #6D2FFF',
                        borderRadius: '50%',
                        filter: 'blur(150px)',
                        zIndex: 0,
                        pointerEvents: 'none',
                     }}
                />
                <Box
                    sx={{
                        width: { xs: 300, md: 414 },
                        height: { xs: 300, md: 414 },
                        left: '35%',
                        top: '70%',
                        transform: 'translate(-50%, -50%)',
                        position: 'absolute',
                        background: '#01DACF',
                        boxShadow: '500px 500px 500px #01DACF',
                        borderRadius: '50%',
                        filter: 'blur(250px)',
                        zIndex: 0,
                        pointerEvents: 'none',
                     }}
                />

                <Drawer
                    variant="permanent"
                    sx={{
                        width: drawerWidth,
                        flexShrink: 0,
                        '& .MuiDrawer-paper': {
                            width: drawerWidth,
                            boxSizing: 'border-box',
                            bgcolor: '#030640',
                            borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                            p: 2,
                            zIndex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                        },
                    }}
                >
                    <Button
                        variant="outlined"
                        startIcon={<Add sx={{ color: '#84EEF2' }} />}
                        onClick={handleNewConversation}
                        fullWidth
                        sx={{
                            mb: 2,
                            borderColor: 'rgba(132, 238, 242, 0.5)',
                            color: 'text.primary',
                            '&:hover': {
                                borderColor: '#84EEF2',
                                bgcolor: 'rgba(132, 238, 242, 0.1)',
                            },
                        }}
                    >
                        New Conversation
                    </Button>
                    <List sx={{ overflowY: 'auto', flexGrow: 1, pr: 0.5 }}>
                        {conversations.map((conv) => (
                            <ListItem
                                key={conv.id}
                                disablePadding
                                sx={{
                                    mb: 0.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    '&:hover .delete-button': {
                                         opacity: 1,
                                     },
                                }}
                                secondaryAction={
                                     <IconButton
                                        edge="end"
                                        aria-label="delete"
                                        size="small"
                                        className="delete-button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteConversation(conv.id);
                                        }}
                                        sx={{
                                            color: 'text.secondary',
                                            opacity: 0.6,
                                            transition: 'opacity 0.2s',
                                            '&:hover': {
                                                color: 'secondary.main',
                                                opacity: 1,
                                            },
                                            mr: -1 
                                        }}
                                    >
                                        <Delete fontSize="small" />
                                    </IconButton>
                                }
                            >
                                <ListItemButton
                                     selected={conv.id === currentConvId}
                                     onClick={() => handleSelectConversation(conv.id)}
                                     sx={{
                                         flexGrow: 1,
                                     }}
                                >
                                    <ListItemText
                                        primary={conv.title}
                                        primaryTypographyProps={{
                                            fontSize: '0.9rem',
                                            color:
                                                conv.id === currentConvId
                                                    ? 'text.primary'
                                                    : 'text.secondary',
                                            whiteSpace: 'nowrap',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            pr: 1,
                                        }}
                                    />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </List>
                </Drawer>

                 <Box
                    sx={{
                        flexGrow: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%',
                        p: { xs: 2, md: 3 },
                        position: 'relative',
                        zIndex: 1,
                        overflow: 'hidden',
                    }}
                >
                     <Box sx={{
                         display: 'flex',
                         flexDirection: 'column',
                         alignItems: 'center',
                         justifyContent: 'center',
                         py: 2,
                         mb: 2,
                         visibility: (!currentConversation || currentConversation.messages.length === 0) && !isFetchingMessages && !isBotLoading ? 'visible' : 'hidden',
                         opacity: (!currentConversation || currentConversation.messages.length === 0) && !isFetchingMessages && !isBotLoading ? 1 : 0,
                         height: (!currentConversation || currentConversation.messages.length === 0) && !isFetchingMessages && !isBotLoading ? 'auto' : 0,
                         transition: 'visibility 0s linear 0.3s, opacity 0.3s ease-out, height 0.3s ease-out',
                         overflow: 'hidden',
                      }}>
                        <img
                            style={{ maxHeight: 260, width: 'auto', objectFit: 'contain', marginBottom: '1rem' }}
                            src="/feeguy-logo.png"
                            alt="FEE.lix Logo"
                        />
                        <Typography variant="h5">
                            Ask FEE.lix anything about Your studies
                        </Typography>
                    </Box>


                    <Box
                        sx={{
                            flexGrow: 1,
                            overflowY: 'auto',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 1.5,
                            pr: 1,
                            mb: 1,
                            position: 'relative',
                        }}
                    >

                        {currentConvId !== null && isFetchingMessages && (
                             <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexGrow: 1}}>
                                <CircularProgress />
                             </Box>
                         )}


                        {currentConversation && currentConversation.messages.length > 0 && !isFetchingMessages && (
                            <>
                                {currentConversation.messages.map((msg) => (
                                    <Paper
                                        key={`${msg.id}-${msg.sender}`}
                                        elevation={0}
                                        sx={{
                                            p: 1.5,
                                            maxWidth: '85%',
                                            alignSelf:
                                                msg.sender === 'user' ? 'flex-end' : 'flex-start',
                                            bgcolor:
                                                msg.sender === 'user'
                                                    ? 'rgba(132, 238, 242, 0.1)'
                                                    : 'rgba(0, 0, 0, 0.25)',
                                            color: 'text.primary',
                                            borderRadius:
                                                msg.sender === 'user'
                                                    ? '12px 12px 2px 12px'
                                                    : '12px 12px 12px 2px',
                                            wordBreak: 'break-word',
                                        }}
                                    >
                                        <Typography
                                            variant="body1"
                                            component="div"
                                            sx={{ whiteSpace: 'pre-wrap' }}
                                        >
                                            {msg.text}
                                        </Typography>
                                        {msg.sender === 'bot' && (
                                            <Box
                                                sx={{
                                                     display: 'flex',
                                                    gap: 0.5,
                                                    mt: 0.5,
                                                    justifyContent: 'flex-start',
                                                }}
                                            >
                                                <IconButton
                                                    size="small"
                                                    onClick={() => handleRating(msg.id, 'up')}
                                                    sx={{
                                                        p: 0.5,
                                                        color: msg.rating === 'up' ? 'success.main' : '#757575',
                                                        '&:hover': { bgcolor: msg.rating !== 'up' ? 'rgba(76, 175, 80, 0.1)' : undefined }
                                                    }}
                                                >
                                                    <ThumbUp sx={{ fontSize: '1rem' }} />
                                                </IconButton>
                                                <IconButton
                                                    size="small"
                                                    onClick={() => handleRating(msg.id, 'down')}
                                                    sx={{
                                                        p: 0.5,
                                                        color: msg.rating === 'down' ? 'error.main' : '#757575',
                                                         '&:hover': { bgcolor: msg.rating !== 'down' ? 'rgba(244, 67, 54, 0.1)' : undefined }
                                                    }}
                                                >
                                                    <ThumbDown sx={{ fontSize: '1rem' }} />
                                                </IconButton>
                                            </Box>
                                        )}
                                    </Paper>
                                ))}
                                {isBotLoading && !isFetchingMessages && (
                                    <Box sx={{ display: 'flex', justifyContent: 'flex-start', py: 1, pl: 1.5 }}> 
                                        <CircularProgress size={24} sx={{ color: 'text.secondary' }} />
                                    </Box>
                                )}
                                <div ref={messagesEndRef} style={{ height: '1px' }} />
                            </>
                        )}

                        {currentConversation && currentConversation.messages.length === 0 && !isFetchingMessages && !isBotLoading && (
                             <Box
                                sx={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'flex-start',
                                    p: 2,
                                    pt: 0,
                                    flexGrow: 1,
                                }}
                            >
                                <Box
                                    sx={{
                                        display: 'flex',
                                        flexWrap: 'wrap',
                                        justifyContent: 'center',
                                        gap: 1.5,
                                        width: '100%',
                                        maxWidth: 900,
                                        margin: '0 auto',
                                    }}
                                >
                                    {[
                                        "What can I ask you to do?",
                                        "Are there any mental health services available for students?",
                                        "How many Red Bulls is it safe to consume per hour of sleep?",
                                    ].map((text, index) => (
                                        <Button
                                            key={index}
                                            variant="contained"
                                            onClick={() => handleSuggestionClick(text)}
                                            sx={{
                                                background: 'rgba(255, 255, 255, 0.15)',
                                                borderRadius: '8px',
                                                color: 'text.primary',
                                                fontSize: 14,
                                                fontWeight: '400',
                                                p: '8px 15px',
                                                flexGrow: { xs: 1, sm: 0 },
                                                textAlign: 'left',
                                                '&:hover': {
                                                    background: 'rgba(255, 255, 255, 0.25)',
                                                    boxShadow: 'none',
                                                },
                                                boxShadow: 'none',
                                            }}
                                        >
                                            {text}
                                        </Button>
                                    ))}
                                </Box>
                            </Box>
                        )}


                         {currentConvId === null && !isFetchingMessages && !isBotLoading && (
                            <Typography variant="body1" sx={{ alignSelf: 'center', m: 'auto', color: 'text.secondary' }}>
                                {conversations.length > 0 ? 'Select or start a conversation.' : 'Start a new conversation!'}
                            </Typography>
                        )}


                    </Box>

                    {currentConvId !== null && (
                        <Box
                            sx={{
                                display: 'flex',
                                gap: 1,
                                alignItems: 'center',
                                flexShrink: 0,
                                p: 1,
                                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                                mt: 'auto',
                            }}
                        >
                            <TextField
                                multiline
                                fullWidth
                                maxRows={5}
                                placeholder="Ask me anything..."
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSend();
                                    }
                                }}
                                disabled={isBotLoading || isFetchingMessages}
                                sx={{ '& .MuiInputBase-root': { bgcolor: 'rgba(0,0,0, 0.2)' } }}
                            />
                            <IconButton
                                color="primary"
                                onClick={handleSend}
                                disabled={!newMessage.trim() || isBotLoading || isFetchingMessages}
                                sx={{
                                    bgcolor: 'primary.main',
                                    borderRadius: '8px',
                                    width: 42,
                                    height: 42,
                                    '&:hover': {
                                        bgcolor: 'primary.dark',
                                    },
                                    '&.Mui-disabled': {
                                        background: 'rgba(124, 115, 255, 0.2)',
                                        '& .MuiSvgIcon-root': {
                                             color: 'rgba(255, 255, 255, 0.3)',
                                        },
                                    },
                                }}
                            >
                                <SendIcon sx={{ color: '#FFF', fontSize: 20 }} />
                            </IconButton>
                        </Box>
                    )}
                </Box>
            </Box>
        </ThemeProvider>
    );
};

export default ChatUI;