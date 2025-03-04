import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  VStack,
  Heading,
  Text,
  useToast,
  FormErrorMessage,
  HStack,
  Tooltip,
  Icon,
  Alert,
  AlertIcon
} from '@chakra-ui/react';
import { InfoIcon } from '@chakra-ui/icons';
import { UserInfo } from '../types';

interface UserInfoFormProps {
  onFormSubmit: (userInfo: UserInfo) => void;
}

// Options for the form dropdowns
const NAME_PREFIXES = ['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.'];

const PURPOSE_OPTIONS = [
  { value: 'networking', label: 'Professional Networking' },
  { value: 'recruiting', label: 'Recruitment/Hiring' },
  { value: 'curious', label: 'Personal Interest' },
  { value: 'technical', label: 'Technical Assessment' },
  { value: 'other', label: 'Other' }
];

const JOB_ROLE_OPTIONS = [
  { value: 'recruiter', label: 'Recruiter/HR Professional' },
  { value: 'hiring_manager', label: 'Hiring Manager' },
  { value: 'software_engineer', label: 'Software Engineer/Developer' },
  { value: 'data_scientist', label: 'Data Scientist/ML Engineer' },
  { value: 'product_manager', label: 'Product Manager' },
  { value: 'engineering_manager', label: 'Engineering Manager' },
  { value: 'executive', label: 'Executive (CTO, CIO, CEO, etc.)' },
  { value: 'technical_lead', label: 'Technical Lead/Architect' },
  { value: 'student', label: 'Student' },
  { value: 'professor', label: 'Professor/Educator' },
  { value: 'researcher', label: 'Researcher' },
  { value: 'other', label: 'Other' }
];

export const UserInfoForm: React.FC<UserInfoFormProps> = ({ onFormSubmit }) => {
  const [userInfo, setUserInfo] = useState<UserInfo & { namePrefix: string; companyType: string }>({
    name: '',
    namePrefix: '',
    email: '',
    companyName: '',
    companyType: '',
    purpose: '',
    jobRole: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formSubmitted, setFormSubmitted] = useState(false);
  const toast = useToast();

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setUserInfo(prev => ({ ...prev, [name]: value }));
    
    // Clear error when field is updated
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitted(true);
    
    // Validate form
    const newErrors: Record<string, string> = {};
    
    if (!userInfo.namePrefix) {
      newErrors.namePrefix = 'Title is required';
    }
    
    if (!userInfo.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!userInfo.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(userInfo.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!userInfo.companyName.trim()) {
      newErrors.companyName = 'Organization name is required';
    }
    
    if (!userInfo.purpose) {
      newErrors.purpose = 'Purpose is required';
    }
    
    if (!userInfo.jobRole) {
      newErrors.jobRole = 'Job role is required';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      window.scrollTo(0, 0);
      return;
    }
    
    // Generate a sessionId (timestamp + random string)
    const sessionId = `${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
    
    // Format the full name with prefix
    const fullName = userInfo.namePrefix ? `${userInfo.namePrefix} ${userInfo.name}` : userInfo.name;
    
    // Submit the form with additional fields
    onFormSubmit({
      name: fullName,
      email: userInfo.email,
      companyName: userInfo.companyName,
      companyType: "", // Sending empty string for companyType
      purpose: userInfo.purpose,
      jobRole: userInfo.jobRole,
      sessionId
    });
    
    toast({
      title: 'Welcome!',
      description: `Thanks for providing your information, ${fullName}!`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Box
      maxW="md"
      mx="auto"
      mt={10}
      p={8}
      borderWidth={1}
      borderRadius="lg"
      boxShadow="lg"
    >
      <VStack spacing={6} align="stretch">
        <Heading size="lg" textAlign="center">Welcome!</Heading>
        <Text textAlign="center">
          Please provide some information before chatting with the resume assistant.
        </Text>
        
        {formSubmitted && Object.keys(errors).length > 0 && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            Please fill out all required fields correctly.
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <VStack spacing={4}>
            <FormControl isRequired isInvalid={!!errors.namePrefix || !!errors.name}>
              <FormLabel>Your Name</FormLabel>
              <HStack>
                <Select 
                  name="namePrefix"
                  placeholder="Title"
                  value={userInfo.namePrefix}
                  onChange={handleChange}
                  width="30%"
                >
                  {NAME_PREFIXES.map(prefix => (
                    <option key={prefix} value={prefix}>{prefix}</option>
                  ))}
                </Select>
                <Input 
                  name="name"
                  placeholder="Full name"
                  value={userInfo.name}
                  onChange={handleChange}
                  width="70%"
                />
              </HStack>
              {errors.namePrefix && <FormErrorMessage>{errors.namePrefix}</FormErrorMessage>}
              {errors.name && <FormErrorMessage>{errors.name}</FormErrorMessage>}
            </FormControl>
            
            <FormControl isRequired isInvalid={!!errors.email}>
              <FormLabel>Email</FormLabel>
              <Input 
                name="email"
                type="email"
                placeholder="you@example.com"
                value={userInfo.email}
                onChange={handleChange}
              />
              {errors.email && <FormErrorMessage>{errors.email}</FormErrorMessage>}
            </FormControl>
            
            <FormControl isRequired isInvalid={!!errors.companyName}>
              <FormLabel>Organization</FormLabel>
              <Input 
                name="companyName"
                placeholder="Company name"
                value={userInfo.companyName}
                onChange={handleChange}
              />
              {errors.companyName && <FormErrorMessage>{errors.companyName}</FormErrorMessage>}
            </FormControl>
            
            <FormControl isRequired isInvalid={!!errors.purpose}>
              <FormLabel>
                Purpose 
                <Tooltip hasArrow label="Why are you interested in Blake's resume?">
                  <Icon as={InfoIcon} ml={1} w={3} h={3} />
                </Tooltip>
              </FormLabel>
              <Select 
                name="purpose"
                placeholder="Select your purpose"
                value={userInfo.purpose}
                onChange={handleChange}
              >
                {PURPOSE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>
              {errors.purpose && <FormErrorMessage>{errors.purpose}</FormErrorMessage>}
            </FormControl>
            
            <FormControl isRequired isInvalid={!!errors.jobRole}>
              <FormLabel>
                Job Role
                <Tooltip hasArrow label="What is your professional role?">
                  <Icon as={InfoIcon} ml={1} w={3} h={3} />
                </Tooltip>
              </FormLabel>
              <Select 
                name="jobRole"
                placeholder="Select your job role"
                value={userInfo.jobRole}
                onChange={handleChange}
              >
                {JOB_ROLE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>
              {errors.jobRole && <FormErrorMessage>{errors.jobRole}</FormErrorMessage>}
            </FormControl>
            
            <Button 
              colorScheme="blue" 
              type="submit"
              width="full"
              mt={4}
              size="lg"
            >
              Start Chatting
            </Button>
          </VStack>
        </form>
      </VStack>
    </Box>
  );
}; 