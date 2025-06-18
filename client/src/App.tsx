import Document from "./Document";
import { useEffect, useState } from "react";
import axios from "axios";
import LoadingOverlay from "./internal/LoadingOverlay";

const BACKEND_URL = "http://localhost:8000";

// ===== TASK 1: DOCUMENT VERSIONING - New TypeScript Interfaces for Versioning =====
interface DocumentVersion {
  version: number;
  created_at: string;
}

interface DocumentVersionsResponse {
  document_id: number;
  versions: DocumentVersion[];
  latest_version: number;
}
// ===== END TASK 1 =====

function App() {
  const [currentDocumentContent, setCurrentDocumentContent] =
    useState<string>("");
  const [currentDocumentId, setCurrentDocumentId] = useState<number>(0);

  // ===== TASK 1: DOCUMENT VERSIONING - New State Variables for Version Management =====
  const [currentVersion, setCurrentVersion] = useState<number>(1);
  const [availableVersions, setAvailableVersions] = useState<DocumentVersion[]>(
    []
  );
  // ===== END TASK 1 =====

  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Load the first patent on mount
  useEffect(() => {
    loadPatent(1);
  }, []);

  // ===== TASK 1: DOCUMENT VERSIONING - Load Available Versions When Document Changes =====
  // Load available versions when document changes
  useEffect(() => {
    if (currentDocumentId > 0) {
      loadVersions(currentDocumentId);
    }
  }, [currentDocumentId]);

  // Callback to load available versions
  const loadVersions = async (documentId: number) => {
    try {
      const response = await axios.get<DocumentVersionsResponse>(
        `${BACKEND_URL}/document/${documentId}/versions`
      );
      setAvailableVersions(response.data.versions);
    } catch (error) {
      console.error("Error loading versions:", error);
      setAvailableVersions([]);
    }
  };
  // ===== END TASK 1 =====

  // ===== TASK 1: DOCUMENT VERSIONING - Enhanced Load Patent with Version Support =====
  // Callback to load a patent from the backend
  const loadPatent = async (documentNumber: number, version?: number) => {
    setIsLoading(true);
    console.log("Loading patent:", documentNumber, "version:", version);
    try {
      const url = version
        ? `${BACKEND_URL}/document/${documentNumber}?version=${version}`
        : `${BACKEND_URL}/document/${documentNumber}`;

      const response = await axios.get(url);
      setCurrentDocumentContent(response.data.content);
      setCurrentDocumentId(documentNumber);
      setCurrentVersion(response.data.version); // Track current version
    } catch (error) {
      console.error("Error loading document:", error);
    }
    setIsLoading(false);
  };

  // Callback to load a specific version
  const loadVersion = async (version: number) => {
    if (currentDocumentId > 0) {
      await loadPatent(currentDocumentId, version);
    }
  };
  // ===== END TASK 1 =====

  // ===== TASK 1: DOCUMENT VERSIONING - Enhanced Save with Version Support =====
  // Callback to persist a patent in the DB (update existing version)
  const savePatent = async () => {
    if (currentDocumentId === 0) return;

    setIsLoading(true);
    try {
      await axios.post(
        `${BACKEND_URL}/save/${currentDocumentId}?version=${currentVersion}`,
        {
          content: currentDocumentContent,
        }
      );
      console.log("Document saved successfully");
    } catch (error) {
      console.error("Error saving document:", error);
    }
    setIsLoading(false);
  };
  // ===== END TASK 1 =====

  // ===== TASK 1: DOCUMENT VERSIONING - New Function to Create New Versions =====
  // Callback to create a new version
  const createNewVersion = async () => {
    if (currentDocumentId === 0) return;

    setIsLoading(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/document/${currentDocumentId}/version`,
        {
          content: currentDocumentContent,
        }
      );

      // Reload versions and switch to the new version
      await loadVersions(currentDocumentId);
      setCurrentVersion(response.data.version);
      console.log("New version created:", response.data.version);
    } catch (error) {
      console.error("Error creating new version:", error);
    }
    setIsLoading(false);
  };
  // ===== END TASK 1 =====

  return (
    <div className="flex flex-col h-full w-full">
      {isLoading && <LoadingOverlay />}
      <header className="flex items-center justify-center top-0 w-full bg-black text-white text-center z-50 mb-[30px] h-[80px]">
        <img src="/si_logo.svg" alt="Logo" style={{ height: "50px" }} />
      </header>
      <div className="flex w-full bg-white h=[calc(100%-100px) gap-4 justify-center box-shadow">
        {/* Left sidebar - Document selection */}
        <div className="flex flex-col h-full items-center gap-2 px-4">
          <button onClick={() => loadPatent(1)}>Patent 1</button>
          <button onClick={() => loadPatent(2)}>Patent 2</button>
        </div>

        {/* Main content area */}
        <div className="flex flex-col h-full items-center gap-2 px-4 flex-1">
          <div className="flex items-center justify-between w-full">
            {/* ===== TASK 1: DOCUMENT VERSIONING - Enhanced Header with Version Display ===== */}
            <h2 className="text-[#213547] opacity-60 text-2xl font-semibold">
              {`Patent ${currentDocumentId} - Version ${currentVersion}`}
            </h2>

            {/* ===== TASK 1: DOCUMENT VERSIONING - Version Selector Dropdown ===== */}
            {/* Version selector */}
            {availableVersions.length > 0 && (
              <div className="flex items-center gap-2">
                <label
                  htmlFor="version-select"
                  className="text-sm font-medium text-gray-700"
                >
                  Version:
                </label>
                <select
                  id="version-select"
                  value={currentVersion}
                  onChange={(e) => loadVersion(parseInt(e.target.value))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  {availableVersions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version} (
                      {new Date(v.created_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>
            )}
            {/* ===== END TASK 1 ===== */}
          </div>

          <Document
            onContentChange={setCurrentDocumentContent}
            content={currentDocumentContent}
          />
        </div>

        {/* Right sidebar - Actions */}
        <div className="flex flex-col h-full items-center gap-2 px-4">
          {/* ===== TASK 1: DOCUMENT VERSIONING - Enhanced Save Button ===== */}
          <button
            onClick={savePatent}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Save
          </button>
          {/* ===== TASK 1: DOCUMENT VERSIONING - New Version Creation Button ===== */}
          <button
            onClick={createNewVersion}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            New Version
          </button>
          {/* ===== END TASK 1 ===== */}
        </div>
      </div>
    </div>
  );
}

export default App;
