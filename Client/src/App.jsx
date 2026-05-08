import { useState, useEffect, useRef } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import { TbAlertTriangleFilled } from "react-icons/tb";
import { MdWarning, MdCheckCircle } from 'react-icons/md';
function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  //  Visualization State 
  const [fileId, setFileId] = useState(null);
  const [totalTimesteps, setTotalTimesteps] = useState(0);
  const [currentTimestep, setCurrentTimestep] = useState(0);
  
  const fileInputRef = useRef(null);

  //  Server Cleanup 
  const cleanupServerCache = async (idToClear) => {
    if (!idToClear) return;
    try {
      await fetch(`http://localhost:8000/cleanup/${idToClear}`, {
        method: 'DELETE',
      });
      console.log(`Successfully cleared server cache for: ${idToClear}`);
    } catch (err) {
      console.error("Failed to clean up server cache", err);
    }
  };

  // Auto-cleanup if the user navigates away or refreshes the page
  useEffect(() => {
    return () => {
      if (fileId) {
        cleanupServerCache(fileId);
      }
    };
  }, [fileId]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      // If there's an existing file ID on the server, delete it before uploading the new one
      if (fileId) cleanupServerCache(fileId);
      
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
      setFileId(null);
      setCurrentTimestep(0);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please select a video file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/analyze/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data.results);
      
      // Save the cache ID and max frames for the visualizer
      setFileId(data.file_id);
      setTotalTimesteps(data.total_timesteps);
      setCurrentTimestep(0);
      
    } catch (err) {
      setError(err.message || "An error occurred during analysis.");
    } finally {
      setLoading(false);
    }
  };

  //Explicit Reset / Clear Button ---
  const handleReset = () => {
    if (fileId) cleanupServerCache(fileId);
    
    setFile(null);
    setResult(null);
    setError(null);
    setFileId(null);
    setTotalTimesteps(0);
    setCurrentTimestep(0);
    
    // Reset the actual HTML file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-screen flex flex-col  bg-gray-100 font-sans">
      <Navbar />
      <main className="pt-12 px-4 sm:px-6 lg:px-8 pb-12">
        <div className="max-w-3xl mx-auto space-y-8"> 
          
          {/* UPLOAD SECTION  */}
          <div className="p-8 bg-white shadow-xl rounded-2xl border border-gray-50">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800 tracking-tight">
                Analyze Video
              </h2>
              <p className="text-sm text-gray-500 mt-2">
                Upload a clip to run it through the anomaly detection model.
              </p>
            </div>
            
            <div className="mb-6 p-8 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-gray-100 hover:border-indigo-400 transition-all duration-200">
              <input 
                type="file" 
                accept="video/*" 
                onChange={handleFileChange} 
                disabled={loading}
                ref={fileInputRef}
                className="block w-full text-sm text-gray-600
                  file:mr-4 file:py-2.5 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-indigo-50 file:text-indigo-700
                  hover:file:bg-indigo-100 cursor-pointer"
              />
            </div>

            <button 
              onClick={handleAnalyze} 
              disabled={!file || loading}
              className={`w-full flex justify-center items-center py-3 px-4 rounded-lg text-white font-bold transition-all ${
                !file || loading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg active:scale-[0.98]'
              }`}
            >
              {loading ? "Extracting Features..." : "Upload & Analyze"}
            </button>

            {error && (
              <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-md">
                <p className="font-bold">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* RESULTS & VISUALIZER SECTION */}
          {result && fileId && (
            <div className="p-8 bg-white shadow-xl rounded-2xl border border-gray-50 animate-fade-in-up">
              
              {/* Top Bar: Results */}
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-200 pb-6 mb-6">
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">Analysis Complete</h3>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-gray-600">Max Score: <span className="font-bold text-gray-900">{(result.max_score * 100).toFixed(2)}%</span></span>
                    {/* <span className="text-gray-600">Mean Score: <span className="font-bold text-gray-900">{(result.mean_score * 100).toFixed(2)}%</span></span> */}
                  </div>
                </div>
                
                <span className={`mt-4 md:mt-0 px-4 py-2 rounded-full text-sm font-bold tracking-wide shadow-sm ${
                  result.is_anomalous 
                    ? 'bg-red-100 text-red-700 border border-red-200' 
                    : 'bg-green-100 text-green-700 border border-green-200'
                }`}>
                  {result.is_anomalous ? (
  <span className="flex items-center gap-2">
    <MdWarning className="text-lg" /> ANOMALOUS ACTIVITY
  </span>
) : (
  <span className="flex items-center gap-2">
    <MdCheckCircle className="text-lg" /> NORMAL
  </span>
)}
                </span>
              </div>

              {/* The Visualizer Media Player */}
              <div className="bg-gray-900 rounded-xl p-6 shadow-inner">
                <h4 className="text-white font-semibold mb-4 flex justify-between items-center">
                  <span>X3D Feature Maps</span>
                  <span className="text-indigo-400 text-sm font-mono">
                    Time Step: {currentTimestep + 1} / {totalTimesteps}
                  </span>
                </h4>
                
                {/* The Image directly from FastAPI */}
                <div className="flex justify-center bg-black rounded-lg overflow-hidden border border-gray-700 mb-6">
                  <img 
                    src={`http://localhost:8000/visualize/${fileId}/${currentTimestep}`} 
                    alt={`Feature maps at time step ${currentTimestep}`}
                    className="max-w-full h-auto object-contain"
                  />
                </div>

                {/* The Scrubber / Slider */}
                <div className="flex items-center gap-4">
                  <span className="text-gray-400 text-sm font-bold">0</span>
                  <input 
                    type="range" 
                    min="0" 
                    max={totalTimesteps - 1} 
                    value={currentTimestep} 
                    onChange={(e) => setCurrentTimestep(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <span className="text-gray-400 text-sm font-bold">{totalTimesteps - 1}</span>
                </div>
              </div>

              {/* Explicit Cleanup Button */}
              <div className="mt-8 flex justify-end">
                <button 
                  onClick={handleReset}
                  className="px-6 py-2 bg-gray-100 hover:bg-red-50 text-gray-600 hover:text-red-600 font-medium rounded-lg transition-colors border border-gray-200 hover:border-red-200"
                >
                  Clear Results & Delete Cache
                </button>
              </div>

            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default App;