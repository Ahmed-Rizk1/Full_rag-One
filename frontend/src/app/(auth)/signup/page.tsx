export default function SignupPage() {
  return (
    <div className="flex h-screen items-center justify-center bg-zinc-950">
      <div className="w-full max-w-md p-8 space-y-6 bg-white/5 border border-white/10 rounded-2xl shadow-2xl backdrop-blur-xl">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-white">Create an account</h1>
          <p className="text-sm text-gray-400 mt-2">Get started with AI Workspace</p>
        </div>
        <form className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-300">Full Name</label>
            <input type="text" className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-300">Email</label>
            <input type="email" className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-300">Password</label>
            <input type="password" className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" />
          </div>
          <button className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20">
            Sign Up
          </button>
        </form>
      </div>
    </div>
  );
}
