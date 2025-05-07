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
  Progress,
} from '@chakra-ui/react';
import { DeleteIcon } from '@chakra-ui/icons';
import { listFiles, deleteDocument, uploadFiles, watchIngestProgress, File } from '../api';

interface FileManagerProps {
  onFileSelect: (fileId: string | undefined) => void;
  selectedFileId?: string;
}

export const FileManager: React.FC<FileManagerProps> = ({
  onFileSelect,
  selectedFileId,
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [phase, setPhase] = useState<"idle"|"upload"|"processing"|"done">("idle");
  const [progress, setProgress] = useState(0);
  const toast = useToast();

  // Move color mode values to the top level
  const boxBg = useColorModeValue('white', 'gray.800');
  const boxBorderColor = useColorModeValue('gray.200', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const SUPPORTED_FILE_TYPES = ['.pdf', '.docx', '.txt'];

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

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

  const validateFiles = (files: FileList): boolean => {
    for (const file of Array.from(files)) {
      const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];
      if (!extension || !SUPPORTED_FILE_TYPES.includes(extension)) {
        toast({
          title: 'Invalid file type',
          description: `File "${file.name}" is not supported. Please upload ${SUPPORTED_FILE_TYPES.join(', ')} files only.`,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        return false;
      }
    }
    return true;
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    if (!validateFiles(files)) {
      event.target.value = ''; // Reset the input
      return;
    }

    setIsLoading(true);
    setPhase("upload");
    setProgress(0);

    try {
      // Handle upload phase
      const uploadId = await uploadFiles(Array.from(files), "default", (phase, pct) => {
        if (phase === "upload") {
          setPhase("upload");
          setProgress(pct);
        } else if (phase === "processing") {
          setPhase("processing");
          setProgress(pct);
        }
      });

      // Handle processing phase
      let stop: (() => void) | undefined;
      stop = watchIngestProgress(uploadId, (phase, pct) => {
        setPhase(phase);
        setProgress(pct);
        if (pct >= 100 && stop) {
          stop();
          setPhase("idle");
          fetchFiles();
          toast({
            title: 'Success',
            description: 'Files uploaded and processed successfully',
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
          event.target.value = ''; // Reset the input after successful upload
          setIsLoading(false);
        }
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload files';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setPhase("idle");
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
        <VStack spacing={2} align="stretch">
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
              accept={SUPPORTED_FILE_TYPES.join(',')}
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </Button>
          <Text fontSize="sm" color="gray.500">
            Supported file types: {SUPPORTED_FILE_TYPES.join(', ')}
          </Text>
        </VStack>

        {phase !== "idle" && (
          <Box data-testid="progress-container">
            <Text mb={2} data-testid="upload-progress-text">
              {phase === "upload" ? "Uploading…" : "Processing…"} {progress}%
            </Text>
            <Progress value={progress} size="sm" colorScheme="blue" />
          </Box>
        )}

        <List spacing={2}>
          <ListItem
            p={2}
            borderRadius="md"
            bg={selectedFileId === undefined ? selectedBg : 'transparent'}
            _hover={{ bg: hoverBg }}
            cursor="pointer"
            onClick={() => onFileSelect(undefined)}
            data-testid="all-files-row"
          >
            <Text fontWeight="medium">All Files</Text>
          </ListItem>
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
                <VStack align="start" spacing={0}>
                  <Text>{file.filename}</Text>
                  <Text fontSize="xs" color="gray.500">
                    {formatFileSize(file.file_size)}
                  </Text>
                </VStack>
                <IconButton
                  aria-label="Delete file"
                  icon={<DeleteIcon />}
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(file.filename);
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