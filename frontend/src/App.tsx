import { useState, useEffect, useRef } from 'react'
import { Box, Container, VStack, useColorModeValue, useToast } from '@chakra-ui/react'
import { Message, UserInfo, FormStatus } from './types'
import { Header } from './components/Header'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { UserInfoForm } from './components/UserInfoForm'

// API endpoints
const API_CHAT_ENDPOINT = '/api/chat';
const API_SAVE_CHAT_ENDPOINT = '/api/save-chat';

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [formStatus, setFormStatus] = useState<FormStatus>('not_submitted')
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const toast = useToast()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Welcome message after form submission
    if (formStatus === 'submitted' && userInfo) {
      setTimeout(() => {
        setMessages([
          {
            content: `Hi ${userInfo.name}! I'm Blake's resume chatbot. Feel free to ask me anything about his experience, skills, or background!\n\n**Here are some questions to get started:**\n\n• What's your career progression in the IoT field?\n• What technologies did you use at Oxy?\n• Tell me about your experience with cloud platforms\n• What was your role at Enchanted Rock?\n• What are your strongest technical skills?`,
            isUser: false,
            timestamp: new Date(),
          },
        ])
      }, 500)
    }
  }, [formStatus, userInfo])

  const handleFormSubmit = (info: UserInfo) => {
    setUserInfo(info)
    setFormStatus('submitted')
  }

  const handleSendMessage = async (message: string) => {
    if (!userInfo) return

    const userMessage = {
      content: message,
      isUser: true,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      const response = await fetch(API_CHAT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: message,
          language: 'en',
          thread_id: userInfo.sessionId,
        }),
      })

      if (!response.ok) throw new Error('Network response was not ok')

      const data = await response.json()
      
      setTimeout(() => {
        setMessages(prev => [
          ...prev,
          {
            content: data.response,
            isUser: false,
            timestamp: new Date(),
          },
        ])
        setIsTyping(false)
      }, 500)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to get response. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
      setIsTyping(false)
    }
  }

  // Handle beforeunload event to save chat log to S3 when user leaves
  useEffect(() => {
    const handleBeforeUnload = async () => {
      if (userInfo && messages.length > 0) {
        try {
          await fetch(API_SAVE_CHAT_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: userInfo.sessionId,
              user_info: userInfo,
              messages: messages.map(msg => ({
                content: msg.content,
                is_user: msg.isUser,
                timestamp: msg.timestamp,
              })),
            }),
          })
        } catch (error) {
          console.error('Failed to save chat log:', error)
        }
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [userInfo, messages])

  return (
    <Box h="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      <Container maxW="container.xl" h="100vh" p={0}>
        <VStack h="full" spacing={0}>
          <Header />
          
          {formStatus === 'not_submitted' ? (
            <UserInfoForm onFormSubmit={handleFormSubmit} />
          ) : (
            <>
              <MessageList
                messages={messages}
                isTyping={isTyping}
                messagesEndRef={messagesEndRef}
              />
              <ChatInput onSendMessage={handleSendMessage} isTyping={isTyping} />
            </>
          )}
        </VStack>
      </Container>
    </Box>
  )
}

export default App 