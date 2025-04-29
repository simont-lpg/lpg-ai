import React, { useEffect, useState } from "react";
import { Box, Text, useColorModeValue, Spinner } from "@chakra-ui/react";
import { getConfig } from "../config";

interface Settings {
  environment: string;
  embedding_model: string;
  generator_model: string;
}

export const EnvStatus: React.FC = () => {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const bg = useColorModeValue("gray.100", "gray.700");
  const color = useColorModeValue("gray.800", "gray.200");

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    fetch(`${getConfig().apiBaseUrl}/settings`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(setSettings)
      .catch((err) => {
        console.error("Error fetching settings:", err);
        setError("Failed to load environment settings");
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <Box p={2} bg={bg} color={color} fontSize="sm" borderRadius="md" shadow="sm" minW="200px">
      {isLoading ? (
        <Box display="flex" alignItems="center" gap={2}>
          <Spinner size="sm" />
          <Text>Loading settings...</Text>
        </Box>
      ) : error ? (
        <Text color="red.500">{error}</Text>
      ) : settings ? (
        <>
          <Text>Environment: {settings.environment}</Text>
          <Text>Embed Model: {settings.embedding_model}</Text>
          <Text>Gen Model: {settings.generator_model}</Text>
        </>
      ) : null}
    </Box>
  );
}; 