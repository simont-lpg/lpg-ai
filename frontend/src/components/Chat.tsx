import React, { useState } from 'react';
import {
  Box,
  VStack,
  Input,
  Button,
  useToast,
  useColorModeValue,
} from '@chakra-ui/react';
import { queryRAG, QueryResponse } from '../api';
import { ChatHistory } from './ChatHistory';

interface Message {
  type: 'user' | 'assistant';
  content: string;
  documents?: QueryResponse['documents'];
  error?: string;
}

interface ChatProps {
  selectedFileId?: string;
}

export const Chat: React.FC<ChatProps> = ({ selectedFileId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const boxBg = useColorModeValue('white', 'gray.800');
  const boxBorderColor = useColorModeValue('gray.200', 'gray.700');

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { type: 'user', content: userMessage }]);

    setIsLoading(true);
    try {
      const response = await queryRAG(userMessage, 3, selectedFileId);
      setMessages((prev) => [
        ...prev,
        {
          type: 'assistant',
          content: response.answers[0] || 'No answer available',
          documents: response.documents,
          error: response.error
        },
      ]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to get response',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box 
      p={4} 
      borderWidth={1} 
      borderRadius="lg" 
      h="100%"
      bg={boxBg}
      borderColor={boxBorderColor}
    >
      <VStack spacing={4} h="100%">
        <Box flex={1} w="100%" overflowY="auto">
          <ChatHistory messages={messages} />
        </Box>

        <Box w="100%">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            mb={2}
          />
          <Button
            colorScheme="blue"
            onClick={handleSend}
            isLoading={isLoading}
            isDisabled={!input.trim() || isLoading}
            w="100%"
          >
            Send
          </Button>
        </Box>
      </VStack>
    </Box>
  );
}; 