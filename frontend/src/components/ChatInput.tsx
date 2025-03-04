import React, { useState } from 'react'
import {
  Box,
  Flex,
  Input,
  IconButton,
  useColorModeValue,
} from '@chakra-ui/react'
import { FaPaperPlane } from 'react-icons/fa'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isTyping: boolean
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isTyping,
}) => {
  const [input, setInput] = useState('')
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return
    onSendMessage(input)
    setInput('')
  }

  return (
    <Box w="full" p={4} bg={bg} borderTop="1px" borderColor={borderColor}>
      <form onSubmit={handleSubmit}>
        <Flex gap={2}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isTyping}
            _disabled={{
              opacity: 0.7,
              cursor: 'not-allowed',
            }}
          />
          <IconButton
            colorScheme="blue"
            aria-label="Send message"
            icon={<FaPaperPlane />}
            type="submit"
            isDisabled={isTyping || !input.trim()}
          />
        </Flex>
      </form>
    </Box>
  )
} 