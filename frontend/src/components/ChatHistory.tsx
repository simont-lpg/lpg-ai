import React from 'react';
import {
  Box,
  Text,
  useColorModeValue,
  VStack,
  Badge,
} from '@chakra-ui/react';
import { QueryResponse } from '../api';

interface ChatHistoryProps {
  messages: Array<{
    type: 'user' | 'assistant';
    content: string;
    documents?: QueryResponse['documents'];
    error?: string;
  }>;
}

const AnswerBubble: React.FC<{ text: string }> = ({ text }) => {
  const bubbleBg = useColorModeValue('blue.50', 'blue.900');
  const textColor = useColorModeValue('gray.800', 'white');

  return (
    <Box
      p={4}
      bg={bubbleBg}
      borderRadius="lg"
      mb={4}
      position="relative"
      data-testid="answer-bubble"
      _before={{
        content: '""',
        position: "absolute",
        top: "-10px",
        left: "50%",
        transform: "translateX(-50%)",
        borderWidth: "5px",
        borderStyle: "solid",
        borderColor: "transparent transparent blue.50 transparent",
      }}
    >
      <Text color={textColor} fontSize="lg">
        {text}
      </Text>
    </Box>
  );
};

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  const sourceBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <VStack spacing={4} align="stretch" data-testid="chat-history">
      {messages.map((message, index) => (
        <Box key={index}>
          <Text fontWeight="bold">
            {message.type === 'user' ? 'You' : 'Assistant'}:
          </Text>
          {message.type === 'assistant' ? (
            <>
              {message.content ? (
                <AnswerBubble text={message.content} />
              ) : (
                <Text fontSize="lg">No answer available</Text>
              )}
              {message.documents && message.documents.length > 0 && (
                <Box mt={2}>
                  <Badge colorScheme="blue" mb={2}>Sources:</Badge>
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
            </>
          ) : (
            <Text fontSize="md">{message.content}</Text>
          )}
          {message.error && (
            <Text color="red.500" fontSize="sm" mt={2}>
              Error: {message.error}
            </Text>
          )}
        </Box>
      ))}
    </VStack>
  );
}; 