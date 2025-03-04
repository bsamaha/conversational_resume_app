import React from 'react'
import { Flex, Box, useColorModeValue } from '@chakra-ui/react'
import { keyframes } from '@emotion/react'

const bounce = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
`

export const TypingIndicator: React.FC = () => {
  const botMessageBg = useColorModeValue('gray.100', 'gray.700')
  const dotColor = useColorModeValue('gray.400', 'gray.500')

  return (
    <Flex justify="flex-start">
      <Box
        bg={botMessageBg}
        p={3}
        borderRadius="lg"
        borderBottomLeftRadius={0}
        maxW="100px"
      >
        <Flex gap={2} align="center">
          <Box
            w="8px"
            h="8px"
            borderRadius="full"
            bg={dotColor}
            animation={`${bounce} 1s infinite`}
          />
          <Box
            w="8px"
            h="8px"
            borderRadius="full"
            bg={dotColor}
            animation={`${bounce} 1s infinite 0.2s`}
          />
          <Box
            w="8px"
            h="8px"
            borderRadius="full"
            bg={dotColor}
            animation={`${bounce} 1s infinite 0.4s`}
          />
        </Flex>
      </Box>
    </Flex>
  )
} 