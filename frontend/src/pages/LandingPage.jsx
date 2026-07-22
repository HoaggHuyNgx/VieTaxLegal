import Hero from '../components/landing/Hero'
import Features from '../components/landing/Features'
import Process from '../components/landing/Process'
import FAQ from '../components/landing/FAQ'
import Footer from '../components/landing/Footer'

export default function LandingPage() {
  return (
    <div id="top">
      <Hero />
      <Features />
      <Process />
      <FAQ />
      <Footer />
    </div>
  )
}
