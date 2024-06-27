const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const app = express();
const port = 3000;

app.use(cors()); // Enable CORS for all routes
app.use(express.json());

app.post('/run-code', (req, res) => {
    const { code } = req.body;
    
    // Write code to a temporary file
    const fs = require('fs');
    fs.writeFileSync('temp.cpp', code);

    // Compile and run the code
    exec('g++ temp.cpp -o temp && ./temp', (error, stdout, stderr) => {
        if (error) {
            res.json({ error: error.message });
            return;
        }
        res.json({ output: stdout });
    });
});

app.post('/run-tests', (req, res) => {
    const { questionId, code } = req.body;
    
    // In a real app, you'd have test cases for each question
    // and run the submitted code against those tests
    res.json({ result: 'Tests not implemented yet' });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
