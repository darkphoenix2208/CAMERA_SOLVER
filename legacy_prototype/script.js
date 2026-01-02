// Get references to HTML elements
const videoElement = document.getElementById('video-feed');
const overlayCanvas = document.getElementById('overlay-canvas');
const overlayCtx = overlayCanvas.getContext('2d');
const gameSelect = document.getElementById('game-select');
const startBtn = document.getElementById('start-scan-btn');
const captureSolveBtn = document.getElementById('capture-solve-btn');
const statusDiv = document.getElementById('status');
const instructionsP = document.getElementById('instructions');

// Detected State Display Elements
const detectedStateArea = document.getElementById('detected-state-area');
const detectedStateDiv = document.getElementById('detected-state');
const detectedStatePlaceholder = document.getElementById('detected-state-placeholder');
const detectedRubiksDiv = document.getElementById('detected-state-rubiks');
const detectedRubiksSpan = document.getElementById('rubiks-string');
const detectedSudokuDiv = document.getElementById('detected-state-sudoku');
const detectedSudokuGrid = document.getElementById('detected-state-sudoku-grid');
const detectedWordSearchDiv = document.getElementById('detected-state-wordsearch');
const detectedWordSearchGrid = document.getElementById('wordsearch-grid');
const detectedWordSearchList = document.getElementById('wordsearch-words');

// Solution Display Elements
const solutionArea = document.getElementById('solution-area');
const solutionDiv = document.getElementById('solution');
const solutionPlaceholder = document.getElementById('solution-placeholder');
const solutionRubiksUl = document.getElementById('solution-steps-rubiks');
const solutionSudokuDiv = document.getElementById('solution-sudoku');
const solutionSudokuGrid = document.getElementById('solution-sudoku-grid');
const solutionWordSearchDiv = document.getElementById('solution-wordsearch');
const solutionWordSearchFound = document.getElementById('solution-wordsearch-found');
const foundWordCountSpan = document.getElementById('found-word-count');

let stream = null;
let processingLoop = null;

// --- 1. Camera Setup ---
async function startCamera() {
    statusDiv.textContent = 'Status: Requesting camera access...';
    if (stream) stopCamera(); // Stop existing stream first

    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment', // Prefer back camera
                width: { ideal: 640 },
                height: { ideal: 480 }
            },
            audio: false
        });
        videoElement.srcObject = stream;
        videoElement.onloadedmetadata = () => {
             // Wait briefly for dimensions to stabilize
            setTimeout(() => {
                const videoWidth = videoElement.videoWidth;
                const videoHeight = videoElement.videoHeight;

                // Set canvas display size based on video element size in the layout
                overlayCanvas.style.width = videoElement.clientWidth + 'px';
                overlayCanvas.style.height = videoElement.clientHeight + 'px';
                // Set canvas internal resolution to match video stream
                overlayCanvas.width = videoWidth;
                overlayCanvas.height = videoHeight;

                updateInstructions(); // Update instructions based on selected game
                statusDiv.textContent = 'Status: Camera active. Position puzzle.';
                startBtn.textContent = 'Stop Camera';
                startBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                startBtn.classList.add('bg-red-600', 'hover:bg-red-700');
                captureSolveBtn.disabled = false;
                startProcessingLoop();
            }, 100); // Small delay might help ensure dimensions are correct
        };
    } catch (err) {
        console.error("Error accessing camera:", err);
        statusDiv.textContent = `Error: ${err.message}. Check permissions.`;
        alert(`Could not access the camera. Error: ${err.message}\nMake sure you are using HTTPS or localhost.`);
        stopCamera(); // Ensure UI resets if camera fails
    }
}

function stopCamera() {
    stopProcessingLoop(); // Stop loop first
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    videoElement.srcObject = null;
    stream = null;
    startBtn.textContent = 'Start Camera';
    startBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
    startBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
    captureSolveBtn.disabled = true;
    statusDiv.textContent = 'Status: Idle';
    if (overlayCtx) {
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height); // Clear canvas
    }
}

// Add toggle behavior to the start/stop button
startBtn.addEventListener('click', () => {
    if (stream) {
        stopCamera();
    } else {
        startCamera();
    }
});

// Update instructions based on selected game
function updateInstructions() {
    const selectedGame = gameSelect.value;
    switch(selectedGame) {
        case 'rubiks':
            instructionsP.textContent = "Show ONE face clearly (e.g., Front). Align within the box. Multi-face scan needed later.";
            break;
        case 'sudoku':
            instructionsP.textContent = "Align the entire Sudoku grid within the box. Ensure good lighting and clear numbers.";
            break;
        case 'wordsearch':
            instructionsP.textContent = "Align the word search grid within the box. Clear letters needed. Word list detection is separate (TBD).";
            break;
        default:
            instructionsP.textContent = "Select a puzzle type.";
    }
     // Also clear previous results when changing game type
    clearResults();
}
gameSelect.addEventListener('change', updateInstructions);

// --- 2. Frame Processing Loop ---
function startProcessingLoop() {
    if (processingLoop) return;

    async function processFrame() {
        if (!stream || !videoElement.srcObject || videoElement.paused || videoElement.ended) {
            stopProcessingLoop(); return;
        };

        // Ensure canvas dimensions match video stream if it changes
        if (overlayCanvas.width !== videoElement.videoWidth || overlayCanvas.height !== videoElement.videoHeight) {
             overlayCanvas.width = videoElement.videoWidth;
             overlayCanvas.height = videoElement.videoHeight;
             // Also update display size to match element size again
             overlayCanvas.style.width = videoElement.clientWidth + 'px';
             overlayCanvas.style.height = videoElement.clientHeight + 'px';
        }

        // Draw mirrored video onto canvas
        overlayCtx.save();
        overlayCtx.scale(-1, 1); // Mirror horizontally
        overlayCtx.drawImage(videoElement, -overlayCanvas.width, 0, overlayCanvas.width, overlayCanvas.height);
        overlayCtx.restore(); // Restore context to normal

        // --- Real-time CV feedback (Phase 2 - Placeholder Box) ---
        const selectedGame = gameSelect.value;
        const boxColor = 'rgba(0, 255, 0, 0.7)'; // Green box
        overlayCtx.strokeStyle = boxColor;
        overlayCtx.lineWidth = 3;
        let targetWidth, targetHeight, targetX, targetY;

        // Calculate target box dimensions based on canvas size (which matches video stream)
        // Keep the box centered
        if (selectedGame === 'sudoku' || selectedGame === 'wordsearch') {
            // Aim for a square box, 80% of the smaller dimension
            const size = Math.min(overlayCanvas.width, overlayCanvas.height) * 0.8;
            targetWidth = size;
            targetHeight = size;
        } else { // rubiks (aim for smaller box for a single face)
            const size = Math.min(overlayCanvas.width, overlayCanvas.height) * 0.5;
            targetWidth = size;
            targetHeight = size;
        }
        targetX = (overlayCanvas.width - targetWidth) / 2;
        targetY = (overlayCanvas.height - targetHeight) / 2;

        overlayCtx.strokeRect(targetX, targetY, targetWidth, targetHeight);

        // Add label above the box
        overlayCtx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        overlayCtx.font = '16px Arial';
        overlayCtx.textAlign = 'center';
        overlayCtx.fillText(`Align ${selectedGame.toUpperCase()} here`, overlayCanvas.width / 2, Math.max(20, targetY - 10)); // Position above box

        processingLoop = requestAnimationFrame(processFrame);
    }
    processingLoop = requestAnimationFrame(processFrame);
}

function stopProcessingLoop() {
    if (processingLoop) {
        cancelAnimationFrame(processingLoop);
        processingLoop = null;
    }
}

// --- 3. Computer Vision - Recognize State (Placeholders - Needs Real Implementation) ---
async function recognizePuzzleState(canvas, gameType) {
    statusDiv.textContent = `Status: Analyzing ${gameType}...`;
    console.log(`Starting recognition for ${gameType}`);
    clearResults(); // Clear previous results before showing new ones
    detectedStatePlaceholder.textContent = 'Analyzing image...'; // Simple loading message

    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate analysis time

    // !!! REPLACE WITH ACTUAL CV LOGIC PER GAME !!!
    try {
        switch (gameType) {
            case 'rubiks':
                console.warn("Rubik's CV not implemented! Using dummy data.");
                // TODO: Use CV to get 54-char state string (requires multi-face scan UI)
                const dummyRubiksState = "DUBUUULDBFRFFRRURFDLDRFDLFDBLULLBDLDBRBRBLLUFFBRDUDDR";
                return { type: 'rubiks', state: dummyRubiksState };
            case 'sudoku':
                console.warn("Sudoku CV not implemented! Using dummy data.");
                // TODO: Use CV (OpenCV.js + Tesseract.js/TF.js) to get 81-char string
                const dummySudokuState = "094000130000000000000070800060000070000608000050000040007030000000000000021000750"; // Use '0' for blanks
                if (dummySudokuState.length !== 81) throw new Error("Detected Sudoku state is not 81 characters.");
                if (!/^[0-9\.]{81}$/.test(dummySudokuState)) throw new Error("Detected Sudoku state contains invalid characters.");
                return { type: 'sudoku', state: dummySudokuState.replace(/\./g, '0') }; // Standardize blanks to '0'
            case 'wordsearch':
                console.warn("Word Search CV not implemented! Using dummy data.");
                // TODO: Use CV (OpenCV.js + Tesseract.js) to get grid (array of strings) and word list (array of strings)
                const dummyWSGrid = ["HELZO", "EWOLD", "LLOAR", "LORDH", "DLROW"];
                const dummyWSWords = ["HELLO", "WORLD", "LORD"];
                return { type: 'wordsearch', grid: dummyWSGrid, words: dummyWSWords };
            default:
                throw new Error(`Unsupported game type for recognition: ${gameType}`);
        }
    } catch (cvError) {
        console.error(`CV Error for ${gameType}:`, cvError);
        throw new Error(`Failed to recognize ${gameType}: ${cvError.message}`); // Re-throw with more context
    }
}

// --- 4. Solver Functions (Placeholders - Needs Real Implementation from Libraries) ---
async function solvePuzzle(puzzleData) {
    statusDiv.textContent = `Status: Solving ${puzzleData.type}...`;
    console.log(`Starting solver for ${puzzleData.type}`);
    await new Promise(resolve => setTimeout(resolve, 50)); // Short delay maybe

    // !!! REPLACE WITH ACTUAL SOLVER LIBRARY CALLS !!!
    try {
        switch (puzzleData.type) {
            case 'rubiks':
                if (typeof solveRubiksCube === 'function') { // Check if solver function exists
                    console.log(`Calling Rubik's solver with state: ${puzzleData.state}`);
                    const solutionMoves = await solveRubiksCube(puzzleData.state); // Use await if it's async
                    if (!solutionMoves || solutionMoves.trim().length === 0) {
                        throw new Error("Solver returned no moves or an empty solution.");
                    }
                    return { type: 'rubiks', steps: solutionMoves.trim().split(/\s+/) };
                } else {
                    // Provide dummy data if function not found, helps UI testing
                    console.error("solveRubiksCube function not found! Returning dummy solution.");
                    return { type: 'rubiks', steps: ["R", "U", "R'", "U'", "(Solver Not Loaded)"] };
                    // throw new Error("Rubik's solver function 'solveRubiksCube' not found.");
                }
            case 'sudoku':
                if (typeof solveSudoku === 'function') { // Check if solver function exists
                    console.log(`Calling Sudoku solver with state: ${puzzleData.state}`);
                    const solvedGridString = solveSudoku(puzzleData.state); // Assumed synchronous
                    if (!solvedGridString) {
                         throw new Error("Sudoku puzzle is invalid or has no solution.");
                    }
                    return { type: 'sudoku', solvedState: solvedGridString };
                } else {
                    // Provide dummy data
                    console.error("solveSudoku function not found! Returning dummy solution.");
                    const dummySolved = puzzleData.state.replace(/0/g, '1'); // Fill blanks with 1
                    return { type: 'sudoku', solvedState: dummySolved };
                    // throw new Error("Sudoku solver function 'solveSudoku' not found.");
                }
            case 'wordsearch':
                if (typeof solveWordSearch === 'function') { // Check if solver function exists
                     console.log(`Calling Word Search solver`);
                    // Assume solveWordSearch returns array like [{word, path: [[r,c],...]}, ...]
                    const foundWordsData = await solveWordSearch(puzzleData.grid, puzzleData.words); // Use await if async
                    if (!foundWordsData || !Array.isArray(foundWordsData)) {
                         throw new Error("Word Search solver failed or returned unexpected data.");
                    }
                    return { type: 'wordsearch', found: foundWordsData };
                } else {
                    // Provide dummy data
                     console.error("solveWordSearch function not found! Returning dummy solution.");
                     return { type: 'wordsearch', found: [{word: 'HELLO', path: [[0,0],[1,0],[2,0],[3,0],[4,0]]}, {word: 'WORLD', path:[[1,1],[2,2],[3,3],[4,4]]}] };
                     // throw new Error("Word Search solver function 'solveWordSearch' not found.");
                }
            default:
                throw new Error(`Unsupported game type for solving: ${puzzleData.type}`);
        }
    } catch(solverError) {
         console.error(`Solver Error for ${puzzleData.type}:`, solverError);
         throw new Error(`Solver failed: ${solverError.message}`); // Re-throw
    }
}

// --- 5. UI Update Functions ---
function clearResults() {
    // Clear detected state
    detectedStatePlaceholder.style.display = 'block';
    detectedRubiksDiv.classList.add('hidden');
    detectedSudokuDiv.classList.add('hidden');
    detectedWordSearchDiv.classList.add('hidden');
    detectedRubiksSpan.textContent = '';
    detectedSudokuGrid.innerHTML = '';
    detectedWordSearchGrid.textContent = '';
    detectedWordSearchList.innerHTML = '';

    // Clear solution
    solutionPlaceholder.style.display = 'block';
    solutionRubiksUl.classList.add('hidden');
    solutionSudokuDiv.classList.add('hidden');
    solutionWordSearchDiv.classList.add('hidden');
    solutionRubiksUl.innerHTML = '';
    solutionSudokuGrid.innerHTML = '';
    solutionWordSearchFound.innerHTML = '';
    if(foundWordCountSpan) foundWordCountSpan.textContent = '0';
}

function displayDetectedState(puzzleData) {
    clearResults(); // Clear everything first
    detectedStatePlaceholder.style.display = 'none'; // Hide placeholder

    if (!puzzleData) {
         detectedStatePlaceholder.textContent = 'Could not detect puzzle state.';
         detectedStatePlaceholder.style.display = 'block';
        return;
    }

    switch (puzzleData.type) {
        case 'rubiks':
            detectedRubiksSpan.textContent = puzzleData.state;
            detectedRubiksDiv.classList.remove('hidden');
            break;
        case 'sudoku':
            detectedSudokuGrid.innerHTML = ''; // Clear previous grid
            for (let i = 0; i < 81; i++) {
                const cell = document.createElement('div');
                cell.textContent = puzzleData.state[i] === '0' ? '' : puzzleData.state[i];
                detectedSudokuGrid.appendChild(cell);
            }
            detectedSudokuDiv.classList.remove('hidden');
            break;
        case 'wordsearch':
            detectedWordSearchGrid.textContent = puzzleData.grid.join('\n');
            detectedWordSearchList.innerHTML = '';
            puzzleData.words.forEach(word => {
                const li = document.createElement('li');
                li.textContent = word;
                detectedWordSearchList.appendChild(li);
            });
            detectedWordSearchDiv.classList.remove('hidden');
            break;
    }
}

function displaySolution(solutionData, originalPuzzleData = null) {
    solutionPlaceholder.style.display = 'none'; // Hide placeholder

    // Hide all solution divs first (already done in clearResults, but safe)
    solutionRubiksUl.classList.add('hidden');
    solutionSudokuDiv.classList.add('hidden');
    solutionWordSearchDiv.classList.add('hidden');

    if (!solutionData) return;

    switch (solutionData.type) {
        case 'rubiks':
            solutionRubiksUl.innerHTML = ''; // Clear previous steps
            solutionData.steps.forEach(step => {
                const li = document.createElement('li');
                li.textContent = step;
                solutionRubiksUl.appendChild(li);
            });
            solutionRubiksUl.classList.remove('hidden');
            break;
        case 'sudoku':
            solutionSudokuGrid.innerHTML = ''; // Clear previous grid
            for (let i = 0; i < 81; i++) {
                const cell = document.createElement('div');
                cell.textContent = solutionData.solvedState[i];
                // Highlight solved cells
                if (originalPuzzleData && originalPuzzleData.state[i] === '0') {
                     cell.classList.add('text-blue-600', 'font-extrabold'); // Style newly filled numbers
                }
                solutionSudokuGrid.appendChild(cell);
            }
             solutionSudokuDiv.classList.remove('hidden');
            break;
        case 'wordsearch':
             solutionWordSearchFound.innerHTML = ''; // Clear previous list
             if(foundWordCountSpan) foundWordCountSpan.textContent = solutionData.found.length;
             // TODO: Highlight paths on canvas using solutionData.found[n].path
             solutionData.found.forEach(found => {
                  const li = document.createElement('li');
                  li.textContent = found.word; // Just list found words for now
                  solutionWordSearchFound.appendChild(li);
             });
            solutionWordSearchDiv.classList.remove('hidden');
            break;
    }
}

function displayError(errorMessage) {
    statusDiv.textContent = `Status: Failed!`;
    clearResults(); // Clear previous results

    // Show error message prominently
    solutionPlaceholder.textContent = `Error: ${errorMessage}`;
    solutionPlaceholder.style.display = 'block';
    solutionPlaceholder.style.color = 'red';
    solutionPlaceholder.style.fontWeight = 'bold';
}

// --- 6. Capture & Solve Orchestrator ---
async function captureAndSolve() {
    if (!stream) { alert("Camera is not active."); return; }
    statusDiv.textContent = 'Status: Capturing frame...';
    captureSolveBtn.disabled = true;
    stopProcessingLoop(); // Pause live processing to grab a stable frame

    // Ensure latest frame is on canvas
    if (overlayCanvas.width !== videoElement.videoWidth || overlayCanvas.height !== videoElement.videoHeight) {
         overlayCanvas.width = videoElement.videoWidth;
         overlayCanvas.height = videoElement.videoHeight;
    }
     overlayCtx.save();
     overlayCtx.scale(-1, 1); // Mirror
     overlayCtx.drawImage(videoElement, -overlayCanvas.width, 0, overlayCanvas.width, overlayCanvas.height);
     overlayCtx.restore(); // Un-mirror context

    const selectedGame = gameSelect.value;
    let puzzleData = null;
    let solutionData = null;

    try {
        clearResults(); // Clear UI before starting analysis

        // --- Run Recognition ---
        puzzleData = await recognizePuzzleState(overlayCanvas, selectedGame);
        displayDetectedState(puzzleData); // Show what was detected

        // --- Run Solver ---
        solutionData = await solvePuzzle(puzzleData); // Pass the detected data
        displaySolution(solutionData, puzzleData); // Pass original data for comparison if needed (e.g., Sudoku highlighting)
        statusDiv.textContent = `Status: Solved!`;

    } catch (err) {
        console.error("Capture/Solve Error:", err);
        displayError(err.message || "An unknown error occurred."); // Display error in UI
    } finally {
        // Re-enable button and restart processing loop
        captureSolveBtn.disabled = false;
        startProcessingLoop(); // Resume live view
    }
}

// --- Event Listeners & Init ---
captureSolveBtn.addEventListener('click', captureAndSolve);
window.addEventListener('beforeunload', stopCamera); // Stop camera when closing tab/reloading
gameSelect.addEventListener('change', updateInstructions);

// Initial setup
updateInstructions(); // Set initial instructions based on default dropdown value
clearResults(); // Ensure results area is clear initially

