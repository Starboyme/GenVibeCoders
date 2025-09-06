import Navbar from "@/components/navbar";
import { Container } from "@/components/container";
export default function Home() {
  return (
    // <div className='flex flex-col items-center h-screen relative [background: radial-gradient(125%_100%_at_50%_0%,_#FFF_6.32%,_#E0F0FF_29.28%,_#E7EFFD_68.68%,_#FFF_100%)]'>
    //   <Container>
    //     <Navbar />
    //     <HomePage />
    //   </Container>
    // </div>
      <div className="flex flex-col items-center h-screen relative [background:radial-gradient(125%_100%_at_50%_0%,_#FFF_6.32%,_#E0F0FF_29.28%,_#E7EFFD_68.68%,_#FFF_100%)]">
        <div className='max-w-7xl mx-auto absolute inset-0 h-full w-full z-0 pointer-events-none'>
          <div className='absolute inset-y-0 left-0 h-full w-px bg-gradient-to-b from-neutral-400/50 via-neutral-200 to-transparent' />
          <div className='absolute inset-y-0 right-0 h-full w-px bg-gradient-to-b from-neutral-300/50 via-neutral-200 to-transparent' />
        </div>
        <Container>
          <Navbar isLoginPage={false} />
        </Container>
    </div>
  );
}
