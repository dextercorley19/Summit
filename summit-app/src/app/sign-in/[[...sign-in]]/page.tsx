import { SignIn } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="mx-auto flex items-center justify-center h-screen">
      <SignIn />
    </div>
  );
}
