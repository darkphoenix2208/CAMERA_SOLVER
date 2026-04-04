import React, { useRef, useState, useEffect } from 'react';
import Webcam from 'react-webcam';
import { api } from '../api';

// --- Styles ---
// Using a dark theme palette
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

const overlayImgStyle = { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' };

const STEPS = [
    { id: 'U', name: 'TOP Face', hint: 'Typically White Center' },
    { id: 'R', name: 'RIGHT Face', hint: 'Typically Red Center' },
    { id: 'F', name: 'FRONT Face', hint: 'Typically Green Center' },
    { id: 'D', name: 'DOWN Face', hint: 'Typically Yellow Center' },
    { id: 'L', name: 'LEFT Face', hint: 'Typically Orange Center' },
    { id: 'B', name: 'BACK Face', hint: 'Typically Blue Center' },
];

export default function RubiksSolver({ onBack }) {
    const webcamRef = useRef(null);

    const [currentStep, setCurrentStep] = useState(-1);
    const [scannedData, setScannedData] = useState({});
    const [currentColors, setCurrentColors] = useState([]);
    const [processedImage, setProcessedImage] = useState(null);
    const [status, setStatus] = useState("Idle");
    const [solution, setSolution] = useState(null);

    const [mode, setMode] = useState('camera');
    const [selectedFile, setSelectedFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);

    const processBlob = async (blob) => {
        setStatus("Processing...");
        try {
            const formData = new FormData();
            formData.append('file', blob, 'img.jpg');
            const res = await api.post('/detect-face', formData);

            if (res.data.success) {
                setProcessedImage(res.data.image);
                if (res.data.colors && res.data.colors.length === 9) {
                    setCurrentColors(res.data.colors);
                    setStatus("Face Detected! Verify colors below.");
                } else {
                    setStatus("Face found, but colors missing?");
                }
            } else {
                setProcessedImage(null);
                setStatus("No face detected. Align cube.");
            }
        } catch (e) {
            console.error(e);
            setStatus("Error " + e.message);
        }
    };

    const solveCube = async () => {
        setStatus("Solving...");
        try {
            const payload = { faces: scannedData };
            const res = await api.post('/solve', payload);

            if (res.data.success) {
                setSolution(res.data.solution);
                setStatus("Solved!");
            } else {
                setStatus("Solver Error: " + res.data.error);
            }
        } catch (e) {
            setStatus("Network Error: " + e.message);
        }
    };

    const handleNext = () => {
        if (currentStep >= 0 && currentStep < 6) {
            const faceId = STEPS[currentStep].id;
            if (currentColors.length !== 9) {
                alert("Please detect a valid face with 9 colors first.");
                return;
            }
            setScannedData(prev => ({ ...prev, [faceId]: currentColors }));
        }

        const next = currentStep + 1;
        setCurrentStep(next);
        setCurrentColors([]);
        setProcessedImage(null);
        setPreviewUrl(null);
        setSelectedFile(null);
        setStatus("Ready for next face.");
    };

    const handleStart = () => setCurrentStep(0);

    const cycleColor = (index) => {
        const map = ['W', 'Y', 'R', 'O', 'G', 'B', 'U'];
        const cur = currentColors[index];
        const i = map.indexOf(cur);
        const nextColor = map[(i + 1) % map.length];
        const newColors = [...currentColors];
        newColors[index] = nextColor;
        setCurrentColors(newColors);
    };

    const renderColorGrid = () => {
        if (currentColors.length === 0) return null;
        const colorMap = { 'W': '#fff', 'Y': '#fbbf24', 'R': '#ef4444', 'O': '#f97316', 'G': '#22c55e', 'B': '#3b82f6', 'U': '#6b7280' };
        return (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '15px' }}>
                {currentColors.map((c, i) => (
                    <div key={i} onClick={() => cycleColor(i)}
                        style={{
                            width: '45px', height: '45px', backgroundColor: colorMap[c],
                            borderRadius: '6px', cursor: 'pointer', border: '2px solid rgba(255,255,255,0.2)',
                            display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#000', fontWeight: 'bold'
                        }}
                    >{c}</div>
                ))}
            </div>
        );
    };

    return (
        <div style={darkCardStyle}>
            <div style={{ width: '100%', display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
                <button onClick={onBack} style={{ background: 'transparent', border: 'none', color: '#ccc', fontSize: '1.5rem', cursor: 'pointer', marginRight: 'auto' }}>←</button>
                <h2 style={{ margin: 0, fontSize: '1.5rem', flex: 1, textAlign: 'center' }}>Rubik's Solver</h2>
                <div style={{ width: '40px' }}></div>
            </div>

            {currentStep === -1 && (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🎲</div>
                    <p style={{ marginBottom: '30px', color: '#9ca3af' }}>Follow the wizard to scan all 6 faces of your cube.</p>
                    <button onClick={handleStart} style={primaryBtnStyle}>Start Scanning</button>
                </div>
            )}

            {currentStep >= 0 && currentStep < 6 && (
                <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '10px', color: '#9ca3af' }}>
                        <span>Step {currentStep + 1} / 6</span>
                        <span style={{ fontWeight: 'bold', color: '#fff' }}>{STEPS[currentStep].name}</span>
                    </div>

                    <div style={{ marginBottom: '15px' }}>
                        <button style={toggleBtnStyle(mode === 'camera')} onClick={() => setMode('camera')}>Camera</button>
                        <button style={toggleBtnStyle(mode === 'upload')} onClick={() => setMode('upload')}>Upload</button>
                    </div>

                    <div style={guideBoxStyle}>
                        {mode === 'camera' ? (
                            <>
                                <Webcam
                                    ref={webcamRef} audio={false} screenshotFormat="image/jpeg"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    videoConstraints={{ facingMode: 'environment' }}
                                />
                                <button onClick={async () => {
                                    const src = webcamRef.current.getScreenshot();
                                    const blob = await (await fetch(src)).blob();
                                    processBlob(blob);
                                }} style={captureBtnStyle}>Capture</button>
                            </>
                        ) : (
                            <div style={{ width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#111', color: '#444' }}>
                                {previewUrl ? <img src={previewUrl} style={{ maxWidth: '100%', maxHeight: '100%' }} /> : "Select Image"}
                            </div>
                        )}
                        {processedImage && <img src={processedImage} style={overlayImgStyle} />}
                    </div>

                    {mode === 'upload' && (
                        <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                            <input type="file" onChange={(e) => {
                                const f = e.target.files[0];
                                if (f) { setSelectedFile(f); setPreviewUrl(URL.createObjectURL(f)); setProcessedImage(null); }
                            }} style={{ color: '#fff' }} />
                            <button onClick={() => selectedFile && processBlob(selectedFile)} disabled={!selectedFile} style={secondaryBtnStyle}>Analyze</button>
                        </div>
                    )}

                    {renderColorGrid()}

                    <div style={{ marginTop: '25px', width: '100%', display: 'flex', justifyContent: 'center' }}>
                        <button onClick={handleNext} disabled={currentColors.length !== 9} style={nextBtnStyle}>
                            {currentStep < 5 ? 'Next Face →' : 'Finish & Solve'}
                        </button>
                    </div>
                    <p style={{ marginTop: '10px', color: '#6b7280', fontSize: '0.9rem' }}>{status}</p>
                </div>
            )}

            {currentStep === 6 && (
                <div style={{ textAlign: 'center', width: '100%' }}>
                    <h3 style={{ marginBottom: '20px' }}>Ready to Solve?</h3>
                    <button onClick={solveCube} style={nextBtnStyle} >Generate Solution</button>

                    {solution && (
                        <div style={{ marginTop: '30px', textAlign: 'left', width: '100%' }}>
                            <div style={{ fontSize: '1.2rem', marginBottom: '10px', color: '#10b981' }}>Solution Found:</div>
                            <div style={{
                                display: 'flex', flexWrap: 'wrap', gap: '10px',
                                background: '#111827', padding: '20px', borderRadius: '12px',
                                fontFamily: 'monospace', fontSize: '1.2rem', color: '#fff', boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)'
                            }}>
                                {solution.map((m, i) => (
                                    <span key={i} style={{ padding: '5px 10px', background: '#374151', borderRadius: '4px' }}>{m}</span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div style={{ marginTop: '40px' }}>
                        <button onClick={() => { setCurrentStep(-1); setScannedData({}); setSolution(null); }} style={secondaryBtnStyle}>Start Over</button>
                    </div>
                </div>
            )}
        </div>
    );
}

// --- Component Styles ---
const primaryBtnStyle = {
    padding: '12px 30px', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: 'white', borderRadius: '12px',
    border: 'none', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', boxShadow: '0 4px 6px rgba(37, 99, 235, 0.3)'
};

const nextBtnStyle = {
    padding: '12px 40px', background: '#10b981', color: 'white', borderRadius: '12px',
    border: 'none', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', opacity: 1, transition: 'opacity 0.2s'
};

const secondaryBtnStyle = {
    padding: '8px 20px', background: '#374151', color: 'white', borderRadius: '8px',
    border: '1px solid #4b5563', cursor: 'pointer'
};

const toggleBtnStyle = (active) => ({
    padding: '8px 20px', margin: '0 5px', borderRadius: '20px', border: 'none',
    background: active ? '#4b5563' : 'transparent', color: active ? '#fff' : '#9ca3af', cursor: 'pointer', fontWeight: 'bold'
});

const captureBtnStyle = {
    position: 'absolute', bottom: '20px', padding: '12px 30px', borderRadius: '30px',
    border: 'none', background: 'white', color: '#000', fontWeight: 'bold', cursor: 'pointer',
    boxShadow: '0 4px 10px rgba(0,0,0,0.5)'
};
