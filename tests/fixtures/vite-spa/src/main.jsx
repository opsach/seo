import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

const Home = () => <main><h1>Invoicing for freelancers</h1><img src="/screenshot.png" /></main>
const Pricing = () => <main><h1>Pricing</h1></main>

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/pricing" element={<Pricing />} />
    </Routes>
  </BrowserRouter>,
)
