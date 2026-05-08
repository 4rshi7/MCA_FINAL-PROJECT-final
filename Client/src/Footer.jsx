export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className=" bg-white  border-t border-gray-200 mt-auto">
      <div className=" max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
        
        <div className=" flex items-center gap-2">
            {/* shield */}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-300" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="text-sm font-semibold text-gray-500">DeepDetect</span>
        </div>

        <p className="text-sm text-gray-400">
          © {currentYear} National Institute of Technology Karnataka.
        </p>

        <div className="flex gap-4 text-sm font-medium text-gray-400">
          <span className="hover:text-indigo-500 cursor-pointer transition-colors">X3D Model</span>
          <span className="hover:text-indigo-500 cursor-pointer transition-colors">STEAD</span>
        </div>
      </div>
    </footer>
  );
}