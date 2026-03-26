'use client'

import { useRef, useMemo, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { useAppStore } from '@/lib/store'

// ─── Waveform Geometry ────────────────────────────────────────────────────────

function WaveformMesh({ isActive }: { isActive: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const materialRef = useRef<THREE.ShaderMaterial>(null)
  const timeRef = useRef(0)

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(16, 4, 256, 32)
    return geo
  }, [])

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uActive: { value: 0 },
        uColor1: { value: new THREE.Color('#FF4D00') },
        uColor2: { value: new THREE.Color('#FF1A1A') },
        uResolution: { value: new THREE.Vector2(1, 1) },
      },
      vertexShader: `
        uniform float uTime;
        uniform float uActive;
        varying vec2 vUv;
        varying float vWave;
        
        float wave(vec2 pos, float freq, float speed, float amp) {
          return sin(pos.x * freq + uTime * speed) * amp;
        }
        
        void main() {
          vUv = uv;
          vec3 pos = position;
          
          float bass = wave(pos.xy, 1.5, 1.2, 0.15 + uActive * 0.3);
          float mid  = wave(pos.xy, 3.0, 2.1, 0.08 + uActive * 0.15);
          float high = wave(pos.xy, 7.0, 3.5, 0.04 + uActive * 0.08);
          
          // Secondary wave along Z
          float waveZ = sin(pos.x * 2.0 + uTime * 0.8) * (0.1 + uActive * 0.2);
          
          pos.y += bass + mid + high;
          pos.z += waveZ;
          vWave = (bass + mid) * 2.0;
          
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform float uActive;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        varying vec2 vUv;
        varying float vWave;
        
        void main() {
          vec3 col = mix(uColor1, uColor2, vUv.x + sin(uTime * 0.5) * 0.2);
          
          // Edge fade
          float edgeFade = smoothstep(0.0, 0.15, vUv.y) * smoothstep(1.0, 0.85, vUv.y);
          float sideFade = smoothstep(0.0, 0.08, vUv.x) * smoothstep(1.0, 0.92, vUv.x);
          
          // Wave luminance
          float luminance = (vWave + 0.5) * 0.6 + uActive * 0.3;
          
          float alpha = edgeFade * sideFade * (0.4 + luminance * 0.6);
          gl_FragColor = vec4(col, alpha * (0.3 + uActive * 0.4));
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  }, [])

  useFrame((state, delta) => {
    timeRef.current += delta
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = timeRef.current
      const targetActive = isActive ? 1.0 : 0.0
      materialRef.current.uniforms.uActive.value = THREE.MathUtils.lerp(
        materialRef.current.uniforms.uActive.value,
        targetActive,
        delta * 2
      )
    }
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(timeRef.current * 0.2) * 0.05
    }
  })

  return (
    <mesh ref={meshRef} geometry={geometry} material={material} rotation={[-0.4, 0, 0]} />
  )
}

// ─── Particle Field ───────────────────────────────────────────────────────────

function ParticleField({ count = 200 }: { count?: number }) {
  const pointsRef = useRef<THREE.Points>(null)
  const timeRef = useRef(0)

  const { positions, sizes } = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    
    for (let i = 0; i < count; i++) {
      positions[i * 3 + 0] = (Math.random() - 0.5) * 20
      positions[i * 3 + 1] = (Math.random() - 0.5) * 8
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10
      sizes[i] = Math.random() * 2 + 0.5
    }
    return { positions, sizes }
  }, [count])

  const particleMaterial = useMemo(() => new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uColor: { value: new THREE.Color('#FF4D00') },
    },
    vertexShader: `
      attribute float size;
      uniform float uTime;
      varying float vAlpha;
      
      void main() {
        vec3 pos = position;
        pos.y += sin(uTime * 0.5 + position.x) * 0.3;
        pos.x += cos(uTime * 0.3 + position.z) * 0.2;
        
        vAlpha = 0.3 + sin(uTime + position.x * 2.0) * 0.2;
        
        vec4 mvPos = modelViewMatrix * vec4(pos, 1.0);
        gl_PointSize = size * (200.0 / -mvPos.z);
        gl_Position = projectionMatrix * mvPos;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vAlpha;
      
      void main() {
        float dist = length(gl_PointCoord - vec2(0.5));
        if (dist > 0.5) discard;
        float strength = 1.0 - (dist * 2.0);
        gl_FragColor = vec4(uColor, strength * vAlpha * 0.6);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  }), [])

  useFrame((state, delta) => {
    timeRef.current += delta
    if (particleMaterial) {
      particleMaterial.uniforms.uTime.value = timeRef.current
    }
    if (pointsRef.current) {
      pointsRef.current.rotation.y += delta * 0.02
    }
  })

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    return geo
  }, [positions, sizes])

  return <points ref={pointsRef} geometry={geometry} material={particleMaterial} />
}

// ─── Camera Controller ────────────────────────────────────────────────────────

function CameraController() {
  const { camera } = useThree()
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth - 0.5) * 2
      mouseRef.current.y = -(e.clientY / window.innerHeight - 0.5) * 2
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  useFrame((state, delta) => {
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouseRef.current.x * 0.5, delta * 2)
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouseRef.current.y * 0.3 + 1, delta * 2)
    camera.lookAt(0, 0, 0)
  })

  return null
}

// ─── Grid Floor ───────────────────────────────────────────────────────────────

function GridFloor() {
  const materialRef = useRef<THREE.ShaderMaterial>(null)
  const timeRef = useRef(0)

  const material = useMemo(() => new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 } },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      varying vec2 vUv;
      
      void main() {
        vec2 grid = abs(fract(vUv * 20.0 - 0.5) - 0.5) / fwidth(vUv * 20.0);
        float line = min(grid.x, grid.y);
        float gridAlpha = 1.0 - min(line, 1.0);
        
        // Fade with distance from center
        float fade = 1.0 - length(vUv - 0.5) * 2.0;
        fade = clamp(fade, 0.0, 1.0);
        
        // Pulse
        float pulse = 0.8 + sin(uTime * 2.0) * 0.2;
        
        vec3 color = vec3(1.0, 0.3, 0.0) * 0.6;
        gl_FragColor = vec4(color, gridAlpha * fade * 0.15 * pulse);
      }
    `,
    transparent: true,
    depthWrite: false,
  }), [])

  useFrame((_, delta) => {
    timeRef.current += delta
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = timeRef.current
    }
  })

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.5, 0]}>
      <planeGeometry args={[30, 30]} />
      <primitive object={material} ref={materialRef} />
    </mesh>
  )
}

// ─── Main Hero Canvas ─────────────────────────────────────────────────────────

export default function HeroCanvas() {
  const phase = useAppStore((s) => s.phase)
  const isActive = ['analyzing', 'generating'].includes(phase)

  return (
    <div className="absolute inset-0 pointer-events-none">
      <Canvas
        camera={{ position: [0, 1, 6], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <CameraController />
        <WaveformMesh isActive={isActive} />
        <ParticleField count={150} />
        <GridFloor />
        <fog attach="fog" args={['#050508', 8, 20]} />
      </Canvas>
    </div>
  )
}
