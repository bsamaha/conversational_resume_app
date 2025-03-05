import React from 'react'
import { Flex, Box, useColorModeValue } from '@chakra-ui/react'
import { Message } from '../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

interface ChatMessageProps {
  message: Message
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const messageBg = useColorModeValue('blue.500', 'blue.400')
  const botMessageBg = useColorModeValue('gray.100', 'gray.700')
  const userTextColor = 'white'
  const botTextColor = useColorModeValue('gray.800', 'gray.100')

  return (
    <Flex justify={message.isUser ? 'flex-end' : 'flex-start'}>
      <Box
        maxW="80%"
        bg={message.isUser ? messageBg : botMessageBg}
        color={message.isUser ? userTextColor : botTextColor}
        p={3}
        borderRadius="lg"
        borderBottomRightRadius={message.isUser ? 0 : 'lg'}
        borderBottomLeftRadius={message.isUser ? 'lg' : 0}
        boxShadow="sm"
      >
        {message.isUser ? (
          <div>{message.content}</div>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]} 
              rehypePlugins={[rehypeHighlight]}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </Box>
    </Flex>
  )
} 