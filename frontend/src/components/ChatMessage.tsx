import React from 'react'
import { Flex, Box, Text, useColorModeValue } from '@chakra-ui/react'
import { Message } from '../types'

interface ChatMessageProps {
  message: Message
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const messageBg = useColorModeValue('blue.500', 'blue.400')
  const botMessageBg = useColorModeValue('gray.100', 'gray.700')

  return (
    <Flex justify={message.isUser ? 'flex-end' : 'flex-start'}>
      <Box
        maxW="80%"
        bg={message.isUser ? messageBg : botMessageBg}
        color={message.isUser ? 'white' : 'inherit'}
        p={3}
        borderRadius="lg"
        borderBottomRightRadius={message.isUser ? 0 : 'lg'}
        borderBottomLeftRadius={message.isUser ? 'lg' : 0}
        boxShadow="sm"
      >
        <Text>{message.content}</Text>
      </Box>
    </Flex>
  )
} 