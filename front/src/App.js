import React, { useState, useEffect } from 'react';

function App() {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [currentQuestionId, setCurrentQuestionId] = useState(1);
  const [question, setQuestion] = useState('');

  const questions = [
    { id: 1, text: 'Write a C++ function to calculate the factorial of a number.' },
    { id: 2, text: 'Implement a C++ function to check if a string is a palindrome.' },
    // Add more questions as needed
  ];

  useEffect(() => {
    loadQuestion(currentQuestionId);
  }, [currentQuestionId]);

  const loadQuestion = (id) => {
    const selectedQuestion = questions.find(q => q.id === id);
    if (selectedQuestion) {
      setQuestion(selectedQuestion.text);
      setCode('// Your C++ code here');
      setOutput('');
    }
  };

  const runCode = async () => {
    setOutput('Running code...');
    try {
      const response = await fetch('http://localhost:8000/run-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setOutput(data.output || data.error);
    } catch (error) {
      setOutput(`Error: ${error.message}. Make sure the backend server is running at http://localhost:8000`);
    }
  };

  const runTests = async () => {
    setOutput('Running tests...');
    try {
      const response = await fetch('http://localhost:8000/run-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ questionId: currentQuestionId, code }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setOutput(`Test results: ${data.result}`);
    } catch (error) {
      setOutput(`Error: ${error.message}. Make sure the backend server is running at http://localhost:8000`);
    }
  };

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-black">C++ Coding Challenges</h1>
        <div className="mb-6 p-4 border-2 border-gray-300">
          <h2 className="text-xl font-semibold mb-2 text-black">Question {currentQuestionId}</h2>
          <p className="text-black">{question}</p>
        </div>
        <div className="mb-6">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-64 p-4 border-2 border-gray-300 font-mono text-sm text-black resize-none"
          />
        </div>
        <div className="flex flex-wrap gap-4 mb-6">
          <button onClick={runCode} className="px-4 py-2 border-2 border-green-300 text-black">Run Code</button>
          <button onClick={runTests} className="px-4 py-2 border-2 border-blue-300 text-black">Run Tests</button>
          <button onClick={() => setCurrentQuestionId(prev => Math.max(1, prev - 1))} className="px-4 py-2 border-2 border-yellow-300 text-black">Previous Question</button>
          <button onClick={() => setCurrentQuestionId(prev => Math.min(questions.length, prev + 1))} className="px-4 py-2 border-2 border-red-300 text-black">Next Question</button>
        </div>
        <pre className="p-4 border-2 border-gray-300 text-black overflow-x-auto">{output}</pre>
      </div>
    </div>
  );
}

export default App;

