import React from 'react'
import { Box, VStack, useColorModeValue } from '@chakra-ui/react'
import { Message } from '../types'
import { ChatMessage } from './ChatMessage'
import { TypingIndicator } from './TypingIndicator'

interface MessageListProps {
  messages: Message[]
  isTyping: boolean
  messagesEndRef: React.RefObject<HTMLDivElement>
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isTyping,
  messagesEndRef,
}) => {
  return (
    <Box
      flex={1}
      w="full"
      overflowY="auto"
      bg={useColorModeValue('gray.50', 'gray.900')}
      p={4}
      css={{
        '&::-webkit-scrollbar': {
          width: '4px',
        },
        '&::-webkit-scrollbar-track': {
          width: '6px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: useColorModeValue('#CBD5E0', '#4A5568'),
          borderRadius: '24px',
        },
      }}
    >
      <VStack spacing={4} align="stretch">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </VStack>
    </Box>
  )
} 