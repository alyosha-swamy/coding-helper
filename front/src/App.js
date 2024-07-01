import React, { useState, useEffect, useCallback } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { cpp } from '@codemirror/lang-cpp';
import { supabase } from './supabaseClient';
import Auth from './components/Auth';
import Papa from 'papaparse';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';

const Alert = ({ children }) => (
  <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-4 dark:bg-blue-900 dark:text-blue-200" role="alert">
    {children}
  </div>
);

function App() {
  const [user, setUser] = useState(null);
  const [code, setCode] = useState('// Your C++ code here');
  const [output, setOutput] = useState('');
  const [currentProblem, setCurrentProblem] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hint, setHint] = useState('');
  const [conversationHistory, setConversationHistory] = useState('');
  const [problems, setProblems] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // Initial width percentage

  useEffect(() => {
    const fetchProblems = async () => {
      try {
        const response = await fetch('/problems.csv');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvString = await response.text();
        const results = Papa.parse(csvString, { header: true });
        setProblems(results.data);
        loadRandomProblem(results.data);
      } catch (error) {
        console.error('Error loading problems:', error);
      }
    };

    fetchProblems();

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    // Load dark mode preference from local storage
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(savedDarkMode);

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    // Apply dark mode class to body
    document.body.classList.toggle('dark', darkMode);
    // Save dark mode preference to local storage
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  const loadRandomProblem = (problemsData) => {
    if (problemsData.length > 0) {
      const randomIndex = Math.floor(Math.random() * problemsData.length);
      const problem = problemsData[randomIndex];
      setCurrentProblem(problem);
      setCode('// Your C++ code here');
      setOutput('');
      setHint('');
      setConversationHistory('');
    }
  };

  const runCode = async () => {
    setIsLoading(true);
    setOutput('Running code...');
    try {
      const response = await fetch('http://localhost:8000/run-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          problem_statement: currentProblem.content,
          expected_output: "Expected output not provided",
          actual_output: output,
          conversation_history: conversationHistory,
          solution: currentProblem['c++']
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
      }
      setOutput(data.output || 'No output');
      setHint(data.response);
      setConversationHistory(prev => `${prev}Tutor: ${data.response}\nStudent: Submitted code\n`);
    } catch (error) {
      setOutput(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const requestHint = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/run-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          problem_statement: currentProblem.content,
          expected_output: "Expected output not provided",
          actual_output: output,
          conversation_history: conversationHistory,
          solution: currentProblem['c++']
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'An error occurred');
      }
      setHint(data.response);
      setConversationHistory(prev => `${prev}Tutor: ${data.response}\nStudent: Requested hint\n`);
    } catch (error) {
      setHint(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  const handleMouseMove = useCallback((e) => {
    const newWidth = (e.clientX / window.innerWidth) * 100;
    setLeftPanelWidth(newWidth);
  }, []);

  const handleMouseUp = useCallback(() => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  }, [handleMouseMove]);

  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  return (
    <div className={`flex flex-col h-screen ${darkMode ? 'dark' : ''}`}>
      <header className="bg-white dark:bg-gray-800 shadow-md p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Get Cracked and High Using AI at DSA</h1>
        <div className="flex items-center">
          <button
            onClick={toggleDarkMode}
            className="mr-4 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-md hover:bg-gray-300 dark:hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-500 focus:ring-opacity-50 shadow"
          >
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
          {user && (
            <button
              onClick={handleSignOut}
              className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 shadow"
            >
              Sign Out
            </button>
          )}
        </div>
      </header>
      <main className="flex-grow flex overflow-hidden bg-gray-100 dark:bg-gray-900">
        {user ? (
          <>
            <div style={{ width: `${leftPanelWidth}%` }} className="flex flex-col p-4">
              {currentProblem && (
                <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-200">{currentProblem.title}</h2>
                  <ReactMarkdown className="text-gray-600 dark:text-gray-300" remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
                    {currentProblem.content}
                  </ReactMarkdown>
                  <p className="text-gray-500 dark:text-gray-400 mt-2">Difficulty: {currentProblem.difficulty}</p>
                </div>
              )}
              <div className="flex-grow overflow-hidden">
                <CodeMirror
                  value={code}
                  height="100%"
                  extensions={[cpp()]}
                  onChange={(value) => setCode(value)}
                  className="border border-gray-300 dark:border-gray-700 rounded-lg shadow h-full"
                  theme={darkMode ? 'dark' : 'light'}
                />
              </div>
            </div>
            <div
              className="w-1 bg-gray-300 cursor-col-resize"
              onMouseDown={handleMouseDown}
            />
            <div style={{ width: `${100 - leftPanelWidth}%` }} className="flex flex-col p-4">
              <div className="flex-grow overflow-auto bg-white dark:bg-gray-800 p-4 rounded-lg shadow mb-4">
                <h3 className="font-semibold mb-2 text-gray-800 dark:text-white">Output:</h3>
                <ReactMarkdown className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap" remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
                  {output}
                </ReactMarkdown>
                {hint && <Alert>{hint}</Alert>}
              </div>
              <div className="flex gap-4">
                <button
                  onClick={runCode}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 shadow"
                  disabled={isLoading}
                >
                  {isLoading ? 'Running...' : 'Submit'}
                </button>
                <button
                  onClick={requestHint}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 shadow"
                  disabled={isLoading}
                >
                  Hint
                </button>
                <button
                  onClick={() => loadRandomProblem(problems)}
                  className="flex-1 px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50 shadow"
                >
                  New Problem
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="w-full flex justify-center items-center">
            <Auth />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

