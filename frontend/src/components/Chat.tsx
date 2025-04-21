import React, { useState } from 'react';
import {
  Box,
  VStack,
  Input,
  Button,
  Text,
  useToast,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import { queryRAG, QueryResponse } from '../api';

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
  
  // Move color mode values to the top level
  const boxBg = useColorModeValue('white', 'gray.800');
  const boxBorderColor = useColorModeValue('gray.200', 'gray.700');
  const sourceBg = useColorModeValue('gray.50', 'gray.700');

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
          {messages.map((message, index) => (
            <Box key={index} mb={4}>
              <Text fontWeight="bold">
                {message.type === 'user' ? 'You' : 'Assistant'}:
              </Text>
              <Text>{message.content}</Text>
              {message.documents && message.documents.length > 0 && (
                <Box mt={2}>
                  <Text fontSize="sm" fontWeight="bold">
                    Sources:
                  </Text>
                  {message.documents.map((doc, idx) => (
                    <Box 
                      key={idx} 
                      mt={1} 
                      p={2} 
                      bg={sourceBg}
                      borderRadius="md"
                    >
                      <Text fontSize="sm">{doc.content}</Text>
                      {doc.score && (
                        <Text fontSize="xs" color="gray.500">
                          Score: {doc.score.toFixed(3)}
                        </Text>
                      )}
                    </Box>
                  ))}
                </Box>
              )}
              {message.error && (
                <Text color="red.500" fontSize="sm" mt={2}>
                  Error: {message.error}
                </Text>
              )}
              <Divider mt={4} />
            </Box>
          ))}
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