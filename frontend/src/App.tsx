import React, { useState } from 'react';
import {
  ChakraProvider,
  Grid,
  GridItem,
  Container,
  IconButton,
  useColorMode,
  Box,
  Image,
  Flex,
  useColorModeValue,
} from '@chakra-ui/react';
import { SunIcon, MoonIcon } from '@chakra-ui/icons';
import { FileManager } from './components/FileManager';
import { Chat } from './components/Chat';
import { EnvStatus } from './components/EnvStatus';
import theme from './theme';
import blackLogo from "./assets/LPG-Full-Black.svg";
import whiteLogo from "./assets/LPG-Full-White.svg";

const ColorModeToggle = () => {
  const { colorMode, toggleColorMode } = useColorMode();
  return (
    <IconButton
      aria-label="Toggle color mode"
      icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
      onClick={toggleColorMode}
    />
  );
};

function App() {
  const [selectedFileId, setSelectedFileId] = useState<string>();
  const { colorMode } = useColorMode();
  const logo = useColorModeValue(blackLogo, whiteLogo);

  return (
    <ChakraProvider theme={theme}>
      <Box minH="100vh" bg={theme.styles.global({ colorMode }).body.bg}>
        <Container maxW="container.xl" py={8}>
          <Flex 
            direction="row" 
            justify="space-between" 
            align="center" 
            mb={6}
            gap={4}
          >
            <Image 
              src={logo}
              alt="LPG Logo"
              h="40px"
              filter="none"
            />
            <EnvStatus />
            <ColorModeToggle />
          </Flex>
          <Grid templateColumns="repeat(2, 1fr)" gap={6} h="calc(100vh - 8rem)">
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
