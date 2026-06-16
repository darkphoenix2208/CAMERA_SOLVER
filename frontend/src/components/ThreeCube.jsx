import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';

// Map Face names to Colors
const colorMap = {
    U: '#ffffff', // White (Top)
    D: '#fbbf24', // Yellow (Bottom)
    F: '#22c55e', // Green (Front)
    B: '#3b82f6', // Blue (Back)
    R: '#ef4444', // Red (Right)
    L: '#f97316'  // Orange (Left)
};

// BoxGeometry faces order: [right, left, top, bottom, front, back]
const getMaterials = (x, y, z) => {
    return [
        new THREE.MeshStandardMaterial({ color: x === 1 ? colorMap.R : '#222' }),
        new THREE.MeshStandardMaterial({ color: x === -1 ? colorMap.L : '#222' }),
        new THREE.MeshStandardMaterial({ color: y === 1 ? colorMap.U : '#222' }),
        new THREE.MeshStandardMaterial({ color: y === -1 ? colorMap.D : '#222' }),
        new THREE.MeshStandardMaterial({ color: z === 1 ? colorMap.F : '#222' }),
        new THREE.MeshStandardMaterial({ color: z === -1 ? colorMap.B : '#222' })
    ];
};

const Cubie = ({ position, rotation, materials }) => {
    return (
        <mesh position={position} rotation={rotation} material={materials}>
            <boxGeometry args={[0.95, 0.95, 0.95]} />
        </mesh>
    );
};

const AnimatedCube = ({ sequence, stepIndex }) => {
    const groupRef = useRef();
    const pivotRef = useRef(new THREE.Group());
    
    // We maintain the 27 cubies in state. Each has a position, rotation, and materials.
    const [cubies, setCubies] = useState(() => {
        let initial = [];
        for (let x = -1; x <= 1; x++) {
            for (let y = -1; y <= 1; y++) {
                for (let z = -1; z <= 1; z++) {
                    initial.push({
                        id: `${x}${y}${z}`,
                        pos: new THREE.Vector3(x, y, z),
                        rot: new THREE.Euler(0, 0, 0),
                        materials: getMaterials(x, y, z)
                    });
                }
            }
        }
        return initial;
    });

    const [animating, setAnimating] = useState(false);
    const [targetRotation, setTargetRotation] = useState(0);
    const [currentRotation, setCurrentRotation] = useState(0);
    const [axis, setAxis] = useState('x');
    const [activeCubies, setActiveCubies] = useState([]);

    // Scramble the cube instantly by applying the solution in reverse
    useEffect(() => {
        if (!sequence || sequence.length === 0) return;
        
        let cbs = [...cubies];
        
        // Reverse sequence
        const revSeq = [...sequence].reverse().map(move => {
            if (move.includes("'")) return move[0];
            if (move.includes("2")) return move;
            return move + "'";
        });

        // Apply instant rotations
        revSeq.forEach(move => {
            const mAxis = getAxis(move[0]);
            const dir = getDirection(move);
            const layer = getLayer(move[0]);
            const angle = dir * (Math.PI / 2);

            cbs = cbs.map(c => {
                if (Math.round(c.pos[mAxis]) === layer) {
                    const obj = new THREE.Object3D();
                    obj.position.copy(c.pos);
                    obj.rotation.copy(c.rot);
                    obj.position.applyAxisAngle(getVector(mAxis), angle);
                    obj.rotateOnWorldAxis(getVector(mAxis), angle);
                    return { ...c, pos: obj.position.clone(), rot: obj.rotation.clone() };
                }
                return c;
            });
        });
        setCubies(cbs);
    }, []); // Run once on mount

    // Watch for stepIndex changes to trigger forward animation
    useEffect(() => {
        if (stepIndex > 0 && stepIndex <= sequence.length && !animating) {
            const move = sequence[stepIndex - 1];
            startAnimation(move);
        }
    }, [stepIndex]);

    const getAxis = (face) => {
        if (face === 'R' || face === 'L') return 'x';
        if (face === 'U' || face === 'D') return 'y';
        if (face === 'F' || face === 'B') return 'z';
    };

    const getLayer = (face) => {
        if (face === 'R' || face === 'U' || face === 'F') return 1;
        if (face === 'L' || face === 'D' || face === 'B') return -1;
    };

    const getDirection = (move) => {
        const face = move[0];
        let sign = 1;
        if (face === 'L' || face === 'D' || face === 'B') sign = -1; // Standard orientation
        
        if (move.includes("'")) sign *= -1;
        if (move.includes("2")) sign *= 2;
        return sign * -1; // WebGL right hand rule adjustment
    };

    const getVector = (ax) => {
        if (ax === 'x') return new THREE.Vector3(1, 0, 0);
        if (ax === 'y') return new THREE.Vector3(0, 1, 0);
        return new THREE.Vector3(0, 0, 1);
    };

    const startAnimation = (move) => {
        const mAxis = getAxis(move[0]);
        const layer = getLayer(move[0]);
        const dir = getDirection(move);
        
        setAxis(mAxis);
        setTargetRotation(dir * (Math.PI / 2));
        setCurrentRotation(0);
        
        const activeIds = cubies.filter(c => Math.round(c.pos[mAxis]) === layer).map(c => c.id);
        setActiveCubies(activeIds);
        
        setAnimating(true);
    };

    useFrame((state, delta) => {
        if (animating) {
            const speed = 4.0;
            const step = Math.sign(targetRotation) * speed * delta;
            
            let newRot = currentRotation + step;
            let finished = false;
            
            if ((targetRotation > 0 && newRot >= targetRotation) || 
                (targetRotation < 0 && newRot <= targetRotation)) {
                newRot = targetRotation;
                finished = true;
            }
            
            pivotRef.current.rotation[axis] = newRot;
            setCurrentRotation(newRot);

            if (finished) {
                // Bake rotation into cubies
                const newCubies = cubies.map(c => {
                    if (activeCubies.includes(c.id)) {
                        const obj = new THREE.Object3D();
                        obj.position.copy(c.pos);
                        obj.rotation.copy(c.rot);
                        obj.position.applyAxisAngle(getVector(axis), targetRotation);
                        obj.rotateOnWorldAxis(getVector(axis), targetRotation);
                        return { ...c, pos: obj.position.clone(), rot: obj.rotation.clone() };
                    }
                    return c;
                });
                
                pivotRef.current.rotation.set(0, 0, 0);
                setCubies(newCubies);
                setAnimating(false);
                setActiveCubies([]);
            }
        }
    });

    return (
        <group ref={groupRef}>
            <group ref={pivotRef}>
                {cubies.filter(c => activeCubies.includes(c.id)).map(c => (
                    <Cubie key={`active-${c.id}`} position={c.pos.toArray()} rotation={c.rot.toArray()} materials={c.materials} />
                ))}
            </group>
            {cubies.filter(c => !activeCubies.includes(c.id)).map(c => (
                <Cubie key={`idle-${c.id}`} position={c.pos.toArray()} rotation={c.rot.toArray()} materials={c.materials} />
            ))}
        </group>
    );
};

export default function ThreeCube({ solution }) {
    const [stepIndex, setStepIndex] = useState(0);

    const handleNext = () => {
        if (stepIndex < solution.length) setStepIndex(stepIndex + 1);
    };
    
    const handlePrev = () => {
        // Simple rewind implies reversing the animation or reloading state.
        // For simplicity, we just allow playing forward step-by-step.
        setStepIndex(0); // Reset
    };

    return (
        <div className="cube-container" style={{ width: '100%', height: '400px', background: '#111', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
            <Canvas camera={{ position: [4, 4, 6], fov: 45 }}>
                <ambientLight intensity={0.7} />
                <directionalLight position={[10, 10, 10]} intensity={1.2} />
                <directionalLight position={[-10, -10, -10]} intensity={0.5} />
                <AnimatedCube sequence={solution} stepIndex={stepIndex} />
                <OrbitControls enablePan={false} enableZoom={true} />
            </Canvas>
            
            <div style={{ position: 'absolute', bottom: '15px', left: '0', width: '100%', display: 'flex', justifyContent: 'center', gap: '15px' }}>
                <button 
                    onClick={handlePrev} 
                    style={{ padding: '8px 16px', background: '#374151', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
                    Restart
                </button>
                <button 
                    onClick={handleNext} 
                    disabled={stepIndex >= solution.length}
                    style={{ padding: '8px 16px', background: stepIndex >= solution.length ? '#4b5563' : '#3b82f6', color: 'white', borderRadius: '8px', border: 'none', cursor: stepIndex >= solution.length ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}>
                    {stepIndex < solution.length ? `Next Move: ${solution[stepIndex]}` : 'Solved!'}
                </button>
            </div>
            
            <div style={{ position: 'absolute', top: '15px', left: '15px', color: 'white', fontWeight: 'bold', background: 'rgba(0,0,0,0.5)', padding: '5px 10px', borderRadius: '6px' }}>
                Step: {stepIndex} / {solution.length}
            </div>
        </div>
    );
}
