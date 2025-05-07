import { SignedIn, SignedOut, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from "next/link";


export default function HomePage() {

  return (
    <>
      <div className="w-screen h-screen flex flex-col items-center justify-center relative">
        <div className="absolute flex flex-col items-center justify-center">
          <h1 className="text-5xl">Summit Agent</h1>
          <SignedOut>
            <h3 className="text-blue-700 text-2xl">
              <SignInButton />
            </h3>
            <h3 className="text-blue-700 text-2xl">
              <SignUpButton />
            </h3>
          </SignedOut>
          <SignedIn>
            <Link href="/dashboard">
              <h3 className="text-blue-700 text-2xl">Dashboard</h3>
            </Link>
          </SignedIn>
        </div>
      </div>
    </>
  );
}
