import React from 'react'
import {
  Flex,
  Box,
  Heading,
  Text,
  IconButton,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react'
import { FaSun, FaMoon, FaUser } from 'react-icons/fa'

export const Header: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode()
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Flex
      w="full"
      justify="space-between"
      align="center"
      p={4}
      borderBottom="1px"
      borderColor={borderColor}
      bg={bg}
    >
      <Flex align="center" gap={3}>
        <Box
          as={FaUser}
          size="40px"
          color={useColorModeValue('blue.500', 'blue.300')}
        />
        <Box>
          <Heading size="md">Conversational Resume</Heading>
          <Text fontSize="sm" color="gray.500">
            Ask me anything about Blake's experience
          </Text>
        </Box>
      </Flex>
      <IconButton
        aria-label="Toggle color mode"
        icon={colorMode === 'light' ? <FaMoon /> : <FaSun />}
        onClick={toggleColorMode}
        variant="ghost"
      />
    </Flex>
  )
} 