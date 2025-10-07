import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import AIChatInterface from './components/AIChatInterface'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div>
   <AIChatInterface/>
    </div>
  )
}

export default App
