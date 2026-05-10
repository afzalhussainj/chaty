import { ChatResponse } from '../types';

export const fetchChatResponse = async (
query: string)
: Promise<ChatResponse> => {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1500));

  const lowerQuery = query.toLowerCase();

  if (lowerQuery.includes('error')) {
    throw new Error('Simulated network error');
  }

  if (
  lowerQuery.includes('alien') ||
  lowerQuery.includes('pizza') ||
  lowerQuery.includes('movie'))
  {
    return {
      answer: '',
      citations: [],
      noResult: true
    };
  }

  if (lowerQuery.includes('handbook') || lowerQuery.includes('rule')) {
    return {
      answer:
      'According to the Student Handbook, all students must adhere to the academic integrity guidelines outlined in Section 4. Violations may result in disciplinary action, including probation or expulsion. Please review the full document for detailed procedures.',
      citations: [
      {
        title: 'Student Handbook 2024-2025',
        url: 'https://university.edu/files/handbook_24_25.pdf',
        source_type: 'pdf',
        page_number: 42
      },
      {
        title: 'Academic Integrity Policy',
        url: 'https://university.edu/policies/academic-integrity',
        source_type: 'html_page',
        page_number: null
      }],

      confidence: 'high'
    };
  }

  if (
  lowerQuery.includes('fee') ||
  lowerQuery.includes('tuition') ||
  lowerQuery.includes('cost'))
  {
    return {
      answer:
      'The tuition fees for the upcoming academic year vary by program. For undergraduate programs, the standard tuition is $15,000 per semester. Additional fees for technology and student services apply. Financial aid and scholarships are available for eligible students.',
      citations: [
      {
        title: 'Tuition and Fees Structure',
        url: 'https://university.edu/admissions/tuition-fees',
        source_type: 'html_page',
        page_number: null
      },
      {
        title: 'Financial Aid Guide',
        url: 'https://university.edu/files/financial_aid_guide.pdf',
        source_type: 'pdf',
        page_number: 12
      }],

      confidence: 'high'
    };
  }

  if (
  lowerQuery.includes('admission') ||
  lowerQuery.includes('apply') ||
  lowerQuery.includes('requirement'))
  {
    return {
      answer:
      'To apply for undergraduate admission, you must submit a completed application form, official high school transcripts, standardized test scores (if applicable), and two letters of recommendation. The early decision deadline is November 1st, and regular decision is January 15th.',
      citations: [
      {
        title: 'Undergraduate Admission Requirements',
        url: 'https://university.edu/admissions/requirements',
        source_type: 'html_page',
        page_number: null
      },
      {
        title: 'Application Deadlines',
        url: 'https://university.edu/admissions/deadlines',
        source_type: 'html_page',
        page_number: null
      }],

      confidence: 'high'
    };
  }

  // Default response
  return {
    answer:
    'The university offers a wide range of academic programs, robust student support services, and a vibrant campus life. I can help you find specific information about admissions, courses, departments, fees, deadlines, policies, or official documents.',
    citations: [
    {
      title: 'University Home Page',
      url: 'https://university.edu',
      source_type: 'html_page',
      page_number: null
    },
    {
      title: 'About the University',
      url: 'https://university.edu/about',
      source_type: 'html_page',
      page_number: null
    }],

    confidence: 'medium'
  };
};