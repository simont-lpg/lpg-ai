import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  IconButton,
  useToast,
  List,
  ListItem,
  useColorModeValue,
} from '@chakra-ui/react';
import { DeleteIcon } from '@chakra-ui/icons';
import { listFiles, deleteDocument, uploadFiles, File } from '../api';

interface FileManagerProps {
  onFileSelect: (fileId: string) => void;
  selectedFileId?: string;
}

export const FileManager: React.FC<FileManagerProps> = ({
  onFileSelect,
  selectedFileId,
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  // Move color mode values to the top level
  const boxBg = useColorModeValue('white', 'gray.800');
  const boxBorderColor = useColorModeValue('gray.200', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const fetchFiles = async () => {
    try {
      const fileList = await listFiles();
      setFiles(fileList);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch files',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsLoading(true);
    try {
      await uploadFiles(files);
      await fetchFiles();
      toast({
        title: 'Success',
        description: 'Files uploaded successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload files',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (fileName: string) => {
    try {
      await deleteDocument(fileName);
      await fetchFiles();
      toast({
        title: 'Success',
        description: 'File deleted successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete file',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  return (
    <Box 
      p={4} 
      borderWidth={1} 
      borderRadius="lg"
      bg={boxBg}
      borderColor={boxBorderColor}
    >
      <VStack spacing={4} align="stretch">
        <Button
          as="label"
          htmlFor="file-upload"
          colorScheme="blue"
          isLoading={isLoading}
        >
          Upload Files
          <input
            id="file-upload"
            type="file"
            multiple
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </Button>

        <List spacing={2}>
          {files.map((file) => (
            <ListItem
              key={file.id}
              p={2}
              borderRadius="md"
              bg={selectedFileId === file.id ? selectedBg : 'transparent'}
              _hover={{ bg: hoverBg }}
              cursor="pointer"
              onClick={() => onFileSelect(file.id)}
            >
              <HStack justify="space-between">
                <Text>{file.name}</Text>
                <IconButton
                  aria-label="Delete file"
                  icon={<DeleteIcon />}
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(file.name);
                  }}
                />
              </HStack>
            </ListItem>
          ))}
        </List>
      </VStack>
    </Box>
  );
}; 