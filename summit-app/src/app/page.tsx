import { Button } from "@/components/ui/button";
import { SignedIn, SignedOut, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from "next/link";


export default function HomePage() {

  return (
    <>
      <div className="w-screen h-screen flex flex-col items-center justify-center relative">
        <div className="absolute flex flex-col items-center justify-center">
          <h1 className="text-5xl">Summit Agent</h1>
          <div className="flex gap-6 pt-6">
            <SignedOut>
              <Button variant="ghost" className="text-cyan-800 text-2xl">
                <SignInButton />
              </Button>
              <Button variant="ghost"  className="text-cyan-800 text-2xl">
                <SignUpButton />
              </Button>
            </SignedOut>
          </div>
          <SignedIn>
            <Link href="/dashboard">
              <Button variant="ghost" className="text-cyan-800 text-2xl">Dashboard</Button>
            </Link>
          </SignedIn>
        </div>
      </div>
    </>
  );
}
