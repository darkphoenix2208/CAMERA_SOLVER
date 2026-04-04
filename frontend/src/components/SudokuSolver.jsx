import React, { useState } from 'react';
import { api } from '../api';

const darkCardStyle = {
    backgroundColor: '#1f2937', color: '#f3f4f6', padding: '20px', borderRadius: '16px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', width: '100%', maxWidth: '800px',
    display: 'flex', flexDirection: 'column', alignItems: 'center'
};

const gridContainerStyle = {
    display: 'grid', gridTemplateColumns: 'repeat(9, 1fr)', gap: '2px',
    backgroundColor: '#374151', border: '4px solid #f472b6', borderRadius: '4px',
    padding: '4px', margin: '20px 0'
};

const inputStyle = (row, col, isOriginal) => {
    // Standard cell border
    const border = '1px solid #374151';

    // Thicker/Brighter borders for 3x3 blocks
    const borderRightStyle = (col + 1) % 3 === 0 && col !== 8 ? '2px solid #f472b6' : border;
    const borderBottomStyle = (row + 1) % 3 === 0 && row !== 8 ? '2px solid #f472b6' : border;

    return {
        width: '100%', aspectRatio: '1/1',
        backgroundColor: '#111827', color: isOriginal ? '#f472b6' : '#fff',
        border: border, // Default border for all sides
        borderRight: borderRightStyle, // Override right border if it's a block boundary
        borderBottom: borderBottomStyle, // Override bottom border if it's a block boundary
        textAlign: 'center',
        fontSize: 'clamp(1rem, 5vw, 1.5rem)', // Responsive font size
        fontWeight: 'bold',
        outline: 'none', caretColor: 'transparent',
        padding: 0, margin: 0
    };
};

const btnStyle = {
    padding: '12px 30px', background: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)', color: 'white', borderRadius: '12px',
    border: 'none', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', boxShadow: '0 4px 6px rgba(236, 72, 153, 0.3)',
    marginTop: '20px'
};

const clearBtnStyle = {
    padding: '8px 20px', background: 'transparent', color: '#9ca3af', borderRadius: '8px',
    border: '1px solid #4b5563', cursor: 'pointer', fontSize: '0.9rem', marginTop: '10px'
};

const initialBoard = Array(9).fill().map(() => Array(9).fill(0));

export default function SudokuSolver({ onBack }) {
    const [board, setBoard] = useState(initialBoard); // 0 = empty
    const [originalMask, setOriginalMask] = useState(Array(9).fill().map(() => Array(9).fill(false))); // true if entered by user
    const [status, setStatus] = useState("Enter numbers & click Solve");

    const handleChange = (r, c, val) => {
        // Validate input 1-9
        if (val === '' || val === '0') {
            const newBoard = [...board];
            newBoard[r] = [...newBoard[r]];
            newBoard[r][c] = 0;
            setBoard(newBoard);

            const newMask = [...originalMask];
            newMask[r][c] = false;
            setOriginalMask(newMask);
            return;
        }

        const num = parseInt(val);
        if (num >= 1 && num <= 9) {
            const newBoard = [...board];
            newBoard[r] = [...newBoard[r]];
            newBoard[r][c] = num;
            setBoard(newBoard);

            const newMask = [...originalMask];
            newMask[r][c] = true;
            setOriginalMask(newMask);
        }
    };

    const handleSolve = async () => {
        setStatus("Solving...");
        try {
            const res = await api.post('/solve-sudoku', { board });
            if (res.data.success) {
                setBoard(res.data.solution);
                setStatus("Solved!");
            } else {
                setStatus(res.data.error || "Unsolvable board");
            }
        } catch (e) {
            setStatus("Error: " + e.message);
        }
    };

    const handleClear = () => {
        setBoard(initialBoard);
        setOriginalMask(Array(9).fill().map(() => Array(9).fill(false)));
        setStatus("Board Cleared");
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setStatus("Extracting Digits...");
        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await api.post('/extract-sudoku', formData);
            if (res.data.success) {
                setBoard(res.data.board);
                // Set mask for non-zero items
                const newMask = res.data.board.map(row => row.map(val => val !== 0));
                setOriginalMask(newMask);
                setStatus("Grid Extracted! Check & Correct errors.");
            } else {
                setStatus("Error: " + res.data.error);
            }
        } catch (err) {
            setStatus("Network Error: " + err.message);
        }
    };

    return (
        <div style={darkCardStyle}>
            <div style={{ width: '100%', display: 'flex', alignItems: 'center' }}>
                <button onClick={onBack} style={{ background: 'transparent', border: 'none', color: '#ccc', fontSize: '1.5rem', cursor: 'pointer', marginRight: 'auto' }}>←</button>
                <h2 style={{ margin: 0, fontSize: '1.5rem', flex: 1, color: '#f472b6', textAlign: 'center' }}>Sudoku Solver</h2>
                <div style={{ width: '40px' }}></div>
            </div>

            {/* Upload Section */}
            <div style={{ margin: '20px 0' }}>
                <label style={{
                    padding: '10px 20px', background: '#374151', color: '#fff', borderRadius: '8px',
                    cursor: 'pointer', border: '1px solid #4b5563', display: 'inline-block'
                }}>
                    📷 Upload Puzzle Image
                    <input type='file' accept='image/*' onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
            </div>

            <div style={{ maxWidth: '400px', width: '100%' }}>
                <div style={gridContainerStyle}>
                    {board.map((row, r) => (
                        row.map((val, c) => (
                            <div key={`${r}-${c}`} style={{ position: 'relative' }}>
                                <input
                                    type="text"
                                    value={val === 0 ? '' : val}
                                    maxLength={1}
                                    onChange={(e) => handleChange(r, c, e.target.value)}
                                    style={inputStyle(r, c, originalMask[r][c])}
                                />
                            </div>
                        ))
                    ))}
                </div>
            </div>

            <p style={{ color: '#d1d5db' }}>{status}</p>

            <button onClick={handleSolve} style={btnStyle}>Solve Puzzle</button>
            <button onClick={handleClear} style={clearBtnStyle}>Clear Board</button>
        </div>
    );
}
