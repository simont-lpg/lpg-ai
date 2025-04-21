import React, { useState } from 'react';
import {
  ChakraProvider,
  Grid,
  GridItem,
  Container,
  IconButton,
  useColorMode,
  Box,
} from '@chakra-ui/react';
import { SunIcon, MoonIcon } from '@chakra-ui/icons';
import { FileManager } from './components/FileManager';
import { Chat } from './components/Chat';
import theme from './theme';

const ColorModeToggle = () => {
  const { colorMode, toggleColorMode } = useColorMode();
  return (
    <IconButton
      aria-label="Toggle color mode"
      icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
      onClick={toggleColorMode}
      position="fixed"
      top={4}
      right={4}
      zIndex={1}
    />
  );
};

function App() {
  const [selectedFileId, setSelectedFileId] = useState<string>();

  return (
    <ChakraProvider theme={theme} resetCSS>
      <Box minH="100vh" bg={theme.styles.global({ colorMode: 'dark' }).body.bg}>
        <Container maxW="container.xl" py={8}>
          <ColorModeToggle />
          <Grid templateColumns="repeat(2, 1fr)" gap={6} h="calc(100vh - 4rem)">
            <GridItem>
              <FileManager
                onFileSelect={setSelectedFileId}
                selectedFileId={selectedFileId}
              />
            </GridItem>
            <GridItem>
              <Chat selectedFileId={selectedFileId} />
            </GridItem>
          </Grid>
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
