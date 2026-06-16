import React, { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import { api } from '../api';

const darkCardStyle = {
    backgroundColor: '#1f2937', color: '#f3f4f6', padding: '20px', borderRadius: '16px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', width: '100%', maxWidth: '800px',
    display: 'flex', flexDirection: 'column', alignItems: 'center'
};

const guideBoxStyle = {
    width: '100%', maxWidth: '640px', aspectRatio: '4/3', position: 'relative', overflow: 'hidden',
    backgroundColor: '#000', borderRadius: '12px', display: 'flex', justifyContent: 'center', alignItems: 'center',
    border: '2px solid #374151', margin: '0 auto'
};

const overlayCanvasStyle = { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' };

export default function SudokuSolver({ onBack }) {
    const webcamRef = useRef(null);
    const canvasRef = useRef(null);

    const [mode, setMode] = useState('camera');
    const [status, setStatus] = useState("Idle");
    const [board, setBoard] = useState(null);
    const [solution, setSolution] = useState(null);
    const [corners, setCorners] = useState(null);
    const [confidence, setConfidence] = useState(0);
    const [solveTimeMs, setSolveTimeMs] = useState(null);
    const [feedbackSent, setFeedbackSent] = useState(false);
    
    const [isScanning, setIsScanning] = useState(true);
    const scanInterval = useRef(null);

    useEffect(() => {
        let active = true;
        const scanLoop = async () => {
            if (!active) return;
            if (webcamRef.current) {
                const src = webcamRef.current.getScreenshot();
                if (src) {
                    try {
                        const blob = await (await fetch(src)).blob();
                        await processFrame(blob);
                    } catch (e) {
                        console.error(e);
                    }
                }
            }
            if (active) {
                scanInterval.current = setTimeout(scanLoop, 600);
            }
        };

        if (mode === 'camera' && isScanning) {
            scanLoop();
        }
        return () => {
            active = false;
            if (scanInterval.current) clearTimeout(scanInterval.current);
        };
    }, [mode, isScanning]);

    // AR Draw Effect
    useEffect(() => {
        if (mode === 'camera' && corners && solution && board) {
            drawAR(corners, board, solution);
        } else if (canvasRef.current) {
            // clear canvas if not ready
            const ctx = canvasRef.current.getContext('2d');
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        }
    }, [corners, solution, board, mode]);

    const drawAR = (corners, originalBoard, solution) => {
        const canvas = canvasRef.current;
        const video = webcamRef.current?.video;
        if (!canvas || !video) return;

        // Match internal canvas resolution to video source resolution
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const pts = corners.map(p => p[0]);
        const [tl, tr, br, bl] = pts;

        const lerp = (p1, p2, t) => [p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t];

        ctx.fillStyle = '#10b981'; // Solved digits in green
        ctx.font = 'bold 32px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Add subtle shadow for visibility
        ctx.shadowColor = 'rgba(0,0,0,0.8)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                if (originalBoard[r][c] === 0) {
                    const digit = solution[r][c];
                    const top = lerp(tl, tr, (c + 0.5) / 9);
                    const bottom = lerp(bl, br, (c + 0.5) / 9);
                    const center = lerp(top, bottom, (r + 0.5) / 9);
                    ctx.fillText(digit.toString(), center[0], center[1]);
                }
            }
        }
        
        ctx.shadowColor = 'transparent'; // reset
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)'; // Translucent blue border
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(tl[0], tl[1]);
        ctx.lineTo(tr[0], tr[1]);
        ctx.lineTo(br[0], br[1]);
        ctx.lineTo(bl[0], bl[1]);
        ctx.closePath();
        ctx.stroke();
    };

    const processFrame = async (blob) => {
        try {
            const formData = new FormData();
            formData.append('file', blob, 'img.jpg');
            const res = await api.post('/extract-sudoku', formData);

            if (res.data.success) {
                const detectedBoard = res.data.board;
                const detCorners = res.data.corners;
                const conf = res.data.confidence || 0;
                setConfidence(conf);
                
                // Check if board has at least some clues (e.g. 10 clues)
                const clues = detectedBoard.flat().filter(d => d !== 0).length;
                if (clues < 10) {
                    setStatus(`Align Sudoku in view... (${Math.round(conf * 100)}% confidence)`);
                    setCorners(null);
                    return;
                }

                setStatus(`Detected ${clues} clues. Solving...`);
                
                // Immediately solve
                const solveRes = await api.post('/solve-sudoku', { board: detectedBoard });
                if (solveRes.data.success) {
                    setBoard(detectedBoard);
                    setSolution(solveRes.data.solution);
                    setCorners(detCorners);
                    setSolveTimeMs(solveRes.data.solve_time_ms);
                    setStatus("✅ Solved! AR Overlay active.");
                } else {
                    setStatus("Detected, but unsolvable.");
                    setCorners(null);
                }
            } else {
                setStatus("Align Sudoku in view...");
                setCorners(null);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setIsScanning(false);
        setStatus("Processing upload...");
        setBoard(null); setSolution(null); setCorners(null); setConfidence(0); setSolveTimeMs(null); setFeedbackSent(false);
        await processFrame(file);
    };

    const submitFeedback = async (isCorrect) => {
        try {
            await api.post('/log-feedback', { puzzle_type: 'sudoku', was_correct: isCorrect });
            setFeedbackSent(true);
        } catch(e) {
            console.error(e);
        }
    };

    const renderGrid = (gridData, isSolution = false) => {
        if (!gridData) return null;
        return (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(9, 1fr)', gap: '2px', background: '#374151', border: '2px solid #4b5563', padding: '4px', marginTop: '20px' }}>
                {gridData.map((row, rIdx) => 
                    row.map((cell, cIdx) => {
                        // If it's a solution grid, color the provided clues differently from the solved ones
                        const isOriginalClue = board && board[rIdx][cIdx] !== 0;
                        const color = cell === 0 ? 'transparent' : (isSolution && !isOriginalClue ? '#10b981' : '#fff');
                        
                        return (
                            <div className="sudoku-cell" key={`${rIdx}-${cIdx}`} style={{
                                width: '30px', height: '30px', background: '#1f2937', display: 'flex', justifyContent: 'center', alignItems: 'center',
                                fontWeight: 'bold', color: color, fontSize: '1.2rem',
                                borderRight: (cIdx === 2 || cIdx === 5) ? '2px solid #4b5563' : 'none',
                                borderBottom: (rIdx === 2 || rIdx === 5) ? '2px solid #4b5563' : 'none',
                            }}>
                                {cell !== 0 ? cell : ''}
                            </div>
                        )
                    })
                )}
            </div>
        );
    };

    return (
        <div className="solver-card" style={darkCardStyle}>
            <div style={{ width: '100%', display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
                <button className="btn-back" onClick={onBack} style={{ background: 'transparent', border: 'none', color: '#ccc', fontSize: '1.5rem', cursor: 'pointer', marginRight: 'auto' }}>←</button>
                <h2 className="header-text" style={{ margin: 0, fontSize: '1.5rem', flex: 1, textAlign: 'center' }}>Sudoku AR Solver</h2>
                <div style={{ width: '40px' }}></div>
            </div>

            <div style={{ marginBottom: '15px' }}>
                <button className="btn-toggle" style={toggleBtnStyle(mode === 'camera')} onClick={() => { setMode('camera'); setIsScanning(true); }}>AR Camera</button>
                <button className="btn-toggle" style={toggleBtnStyle(mode === 'upload')} onClick={() => { setMode('upload'); setIsScanning(false); }}>Upload Image</button>
            </div>

            {mode === 'camera' && (
                <div className="guide-box" style={guideBoxStyle}>
                    <Webcam
                        ref={webcamRef} audio={false} screenshotFormat="image/jpeg"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        videoConstraints={{ facingMode: 'environment' }}
                    />
                    <canvas ref={canvasRef} style={overlayCanvasStyle} />
                    
                    {solution && (
                        <div style={{ position: 'absolute', top: '10px', right: '10px', background: '#10b981', padding: '5px 10px', borderRadius: '8px', fontWeight: 'bold', color: 'white' }}>
                            LOCKED
                        </div>
                    )}
                </div>
            )}

            {mode === 'upload' && (
                <div style={{ width: '100%', textAlign: 'center', marginTop: '20px' }}>
                    <label className="btn-primary" style={primaryBtnStyle}>
                        📷 Choose Image
                        <input type='file' accept='image/*' onChange={handleFileUpload} style={{ display: 'none' }} />
                    </label>
                </div>
            )}

            <p style={{ marginTop: '15px', color: solution ? '#10b981' : '#9ca3af', fontWeight: 'bold' }}>
                {status} {solveTimeMs && `(Solved in ${solveTimeMs}ms)`}
            </p>

            {mode === 'camera' && !solution && isScanning && (
                <div style={{ width: '80%', height: '8px', background: '#374151', borderRadius: '4px', marginTop: '5px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.round(confidence * 100)}%`, background: confidence > 0.8 ? '#10b981' : (confidence > 0.4 ? '#f59e0b' : '#ef4444'), transition: 'width 0.3s' }}></div>
                </div>
            )}

            {mode === 'upload' && solution && (
                <div style={{ marginTop: '20px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <h3 style={{ color: '#fff' }}>Solution</h3>
                    {renderGrid(solution, true)}
                </div>
            )}

            {solution && (
                <div style={{ marginTop: '15px', display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span style={{ color: '#9ca3af' }}>{feedbackSent ? "Thanks for your feedback!" : "Did we get it right?"}</span>
                    {!feedbackSent && (
                        <>
                            <button onClick={() => submitFeedback(true)} style={feedbackBtnStyle}>👍</button>
                            <button onClick={() => submitFeedback(false)} style={feedbackBtnStyle}>👎</button>
                        </>
                    )}
                </div>
            )}
            
            {mode === 'camera' && !isScanning && (
                <button className="btn-secondary" onClick={() => { setIsScanning(true); setBoard(null); setSolution(null); setCorners(null); setConfidence(0); setSolveTimeMs(null); setFeedbackSent(false); }} style={{ ...secondaryBtnStyle, marginTop: '20px' }}>
                    Rescan
                </button>
            )}
        </div>
    );
}

// --- Component Styles ---
const primaryBtnStyle = {
    padding: '12px 30px', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: 'white', borderRadius: '12px',
    border: 'none', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', display: 'inline-block', boxShadow: '0 4px 6px rgba(37, 99, 235, 0.3)'
};

const secondaryBtnStyle = {
    padding: '12px 20px', background: '#374151', color: 'white', borderRadius: '12px',
    border: '1px solid #4b5563', cursor: 'pointer', fontWeight: 'bold'
};

const toggleBtnStyle = (active) => ({
    padding: '8px 20px', margin: '0 5px', borderRadius: '20px', border: 'none',
    background: active ? '#4b5563' : 'transparent', color: active ? '#fff' : '#9ca3af', cursor: 'pointer', fontWeight: 'bold'
});

const feedbackBtnStyle = {
    background: '#374151', border: '1px solid #4b5563', borderRadius: '8px', padding: '6px 12px',
    cursor: 'pointer', fontSize: '1.2rem', transition: 'transform 0.1s'
};
