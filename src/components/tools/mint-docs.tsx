"use client";

import React, { useState, useRef } from "react";
import { 
  FileText, 
  Files, 
  Scissors, 
  Image as ImageIcon, 
  Download, 
  Upload, 
  Trash2, 
  Check, 
  AlertCircle, 
  Loader2, 
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Layers
} from "lucide-react";
import { PDFDocument } from "pdf-lib";
import { toast } from "sonner";

export type MintDocMode = "merge" | "split" | "img2pdf";

export function MintDocs() {
  const [mode, setMode] = useState<MintDocMode>("merge");
  const [isProcessing, setIsProcessing] = useState(false);

  // Merge state
  const [mergeFiles, setMergeFiles] = useState<File[]>([]);
  const mergeInputRef = useRef<HTMLInputElement>(null);

  // Split state
  const [splitFile, setSplitFile] = useState<File | null>(null);
  const [splitTotalPages, setSplitTotalPages] = useState<number>(0);
  const [pageRange, setPageRange] = useState<string>("1-2");
  const splitInputRef = useRef<HTMLInputElement>(null);

  // Images to PDF state
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const imageInputRef = useRef<HTMLInputElement>(null);

  // Handle Merge File Selection
  const handleMergeFilesAdded = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const added = Array.from(e.target.files).filter((f) => f.type === "application/pdf");
      if (added.length === 0) {
        toast("Please select PDF files.");
        return;
      }
      setMergeFiles((prev) => [...prev, ...added]);
    }
  };

  const removeMergeFile = (idx: number) => {
    setMergeFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  // Execute Merge PDFs in Browser
  const executeMerge = async () => {
    if (mergeFiles.length < 2) {
      toast("Select at least 2 PDF files to merge.");
      return;
    }

    setIsProcessing(true);
    try {
      const mergedPdf = await PDFDocument.create();

      for (const file of mergeFiles) {
        const bytes = await file.arrayBuffer();
        const pdf = await PDFDocument.load(bytes);
        const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
        copiedPages.forEach((page) => mergedPdf.addPage(page));
      }

      const mergedBytes = await mergedPdf.save();
      const blob = new Blob([mergedBytes as unknown as BlobPart], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement("a");
      link.href = url;
      link.download = `MintDocs_Merged_${Date.now()}.pdf`;
      link.click();
      URL.revokeObjectURL(url);

      toast("PDFs successfully merged and downloaded!");
    } catch (err) {
      console.error("Failed to merge PDFs", err);
      toast("Unable to merge documents. Ensure files are not password-protected.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Split File Selection
  const handleSplitFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== "application/pdf") {
        toast("Please upload a PDF file.");
        return;
      }
      try {
        const bytes = await file.arrayBuffer();
        const pdf = await PDFDocument.load(bytes);
        setSplitFile(file);
        const count = pdf.getPageCount();
        setSplitTotalPages(count);
        setPageRange(`1-${Math.min(count, 3)}`);
      } catch (err) {
        toast("Could not read PDF. It may be encrypted or corrupted.");
      }
    }
  };

  // Execute Split PDF in Browser
  const executeSplit = async () => {
    if (!splitFile) {
      toast("Please select a PDF file first.");
      return;
    }

    setIsProcessing(true);
    try {
      const bytes = await splitFile.arrayBuffer();
      const srcPdf = await PDFDocument.load(bytes);
      const total = srcPdf.getPageCount();

      // Parse page range: e.g. "1-3, 5, 7"
      const targetIndices: number[] = [];
      const parts = pageRange.split(",").map((s) => s.trim());

      for (const part of parts) {
        if (part.includes("-")) {
          const [startStr, endStr] = part.split("-");
          const start = Math.max(1, parseInt(startStr, 10));
          const end = Math.min(total, parseInt(endStr, 10));
          for (let p = start; p <= end; p++) {
            if (!targetIndices.includes(p - 1)) targetIndices.push(p - 1);
          }
        } else {
          const p = parseInt(part, 10);
          if (p >= 1 && p <= total && !targetIndices.includes(p - 1)) {
            targetIndices.push(p - 1);
          }
        }
      }

      if (targetIndices.length === 0) {
        toast("Invalid page range specified.");
        setIsProcessing(false);
        return;
      }

      targetIndices.sort((a, b) => a - b);

      const newPdf = await PDFDocument.create();
      const copiedPages = await newPdf.copyPages(srcPdf, targetIndices);
      copiedPages.forEach((page) => newPdf.addPage(page));

      const newBytes = await newPdf.save();
      const blob = new Blob([newBytes as unknown as BlobPart], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `MintDocs_Extracted_p${pageRange.replace(/[^0-9-]/g, "_")}.pdf`;
      link.click();
      URL.revokeObjectURL(url);

      toast(`Extracted ${targetIndices.length} page(s) successfully!`);
    } catch (err) {
      console.error("Failed to split PDF", err);
      toast("Failed to extract pages from PDF.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Images to PDF Selection
  const handleImagesAdded = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const imgs = Array.from(e.target.files).filter((f) =>
        ["image/jpeg", "image/png", "image/jpg", "image/webp"].includes(f.type)
      );
      if (imgs.length === 0) {
        toast("Please select image files (JPG, PNG).");
        return;
      }
      setImageFiles((prev) => [...prev, ...imgs]);
    }
  };

  // Convert Images to PDF in Browser
  const executeImagesToPdf = async () => {
    if (imageFiles.length === 0) {
      toast("Please select at least 1 image to convert.");
      return;
    }

    setIsProcessing(true);
    try {
      const pdfDoc = await PDFDocument.create();

      for (const imgFile of imageFiles) {
        const bytes = await imgFile.arrayBuffer();
        let image;
        if (imgFile.type === "image/png") {
          image = await pdfDoc.embedPng(bytes);
        } else {
          image = await pdfDoc.embedJpg(bytes);
        }

        // Standard A4 aspect ratio or image's natural dimensions
        const page = pdfDoc.addPage([image.width, image.height]);
        page.drawImage(image, {
          x: 0,
          y: 0,
          width: image.width,
          height: image.height,
        });
      }

      const pdfBytes = await pdfDoc.save();
      const blob = new Blob([pdfBytes as unknown as BlobPart], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `MintDocs_Images_${Date.now()}.pdf`;
      link.click();
      URL.revokeObjectURL(url);

      toast(`Converted ${imageFiles.length} image(s) to PDF!`);
    } catch (err) {
      console.error("Failed image to PDF conversion", err);
      toast("Failed to convert images to PDF. Ensure images are valid JPG/PNG.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="p-6 md:p-8 rounded-3xl bg-card border border-border shadow-xs space-y-6">
        
        {/* Header & Mode Switcher */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-accent/15 text-accent">
                <FileText className="w-5 h-5" />
              </span>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                MintDocs • 100% Client-Side PDF Tools
              </h2>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>Zero server uploads. All PDF processing happens securely in your browser RAM.</span>
            </p>
          </div>

          {/* Mode Tabs */}
          <div className="flex items-center gap-1 p-1 bg-muted/20 border border-border/80 rounded-xl text-xs font-semibold self-start md:self-auto shrink-0">
            <button
              type="button"
              onClick={() => setMode("merge")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                mode === "merge"
                  ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Files className="w-3.5 h-3.5" />
              <span>Merge PDFs</span>
            </button>

            <button
              type="button"
              onClick={() => setMode("split")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                mode === "split"
                  ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Scissors className="w-3.5 h-3.5" />
              <span>Split / Extract</span>
            </button>

            <button
              type="button"
              onClick={() => setMode("img2pdf")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                mode === "img2pdf"
                  ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              <span>Images &rarr; PDF</span>
            </button>
          </div>
        </div>

        {/* ============================================================== */}
        {/* MODE 1: MERGE PDFS                                            */}
        {/* ============================================================== */}
        {mode === "merge" && (
          <div className="space-y-5">
            <div
              onClick={() => mergeInputRef.current?.click()}
              className="p-8 rounded-2xl border-2 border-dashed border-border/80 hover:border-accent/50 hover:bg-accent/5 transition-all flex flex-col items-center justify-center text-center gap-3 cursor-pointer group"
            >
              <input
                ref={mergeInputRef}
                type="file"
                multiple
                accept="application/pdf"
                onChange={handleMergeFilesAdded}
                className="hidden"
              />
              <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent group-hover:scale-105 transition-transform">
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-bold text-foreground">Click to upload multiple PDFs to merge</p>
                <p className="text-xs text-muted-foreground">Select past question papers, notes, or assignment files</p>
              </div>
            </div>

            {mergeFiles.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
                  <span>Selected Documents ({mergeFiles.length})</span>
                  <button
                    type="button"
                    onClick={() => setMergeFiles([])}
                    className="text-red-500 hover:underline cursor-pointer"
                  >
                    Clear All
                  </button>
                </div>

                <div className="space-y-2">
                  {mergeFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-muted/15 border border-border/60 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <span className="w-5 h-5 rounded-md bg-accent/20 text-accent font-mono text-[10px] font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </span>
                        <span className="font-semibold text-foreground truncate">{file.name}</span>
                        <span className="text-[10px] text-muted-foreground font-mono shrink-0">
                          ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => removeMergeFile(idx)}
                        className="p-1 text-muted-foreground hover:text-red-500 rounded-lg transition-colors cursor-pointer"
                        title="Remove"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  disabled={isProcessing || mergeFiles.length < 2}
                  onClick={executeMerge}
                  className="w-full py-3.5 rounded-2xl bg-foreground text-background font-bold text-xs hover:bg-foreground/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-accent" />
                      <span>Merging documents in browser...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 text-accent" />
                      <span>Merge {mergeFiles.length} PDFs &amp; Download</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* MODE 2: SPLIT / EXTRACT PAGES                                  */}
        {/* ============================================================== */}
        {mode === "split" && (
          <div className="space-y-5">
            {!splitFile ? (
              <div
                onClick={() => splitInputRef.current?.click()}
                className="p-8 rounded-2xl border-2 border-dashed border-border/80 hover:border-accent/50 hover:bg-accent/5 transition-all flex flex-col items-center justify-center text-center gap-3 cursor-pointer group"
              >
                <input
                  ref={splitInputRef}
                  type="file"
                  accept="application/pdf"
                  onChange={handleSplitFileSelected}
                  className="hidden"
                />
                <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent group-hover:scale-105 transition-transform">
                  <Scissors className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-bold text-foreground">Select a PDF to extract pages</p>
                  <p className="text-xs text-muted-foreground">Pull specific units or questions from big syllabus PDFs</p>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-2xl bg-muted/15 border border-border/70 space-y-4">
                <div className="flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <span className="font-bold text-foreground block truncate max-w-md">{splitFile.name}</span>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      {splitTotalPages} Total Pages &bull; {(splitFile.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSplitFile(null)}
                    className="text-red-500 hover:underline text-xs cursor-pointer"
                  >
                    Change PDF
                  </button>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-border/50">
                  <label className="text-xs font-semibold text-foreground">Page Range to Extract</label>
                  <input
                    type="text"
                    value={pageRange}
                    onChange={(e) => setPageRange(e.target.value)}
                    placeholder="e.g. 1-3, 5, 8"
                    className="w-full bg-background border border-border rounded-xl px-3.5 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Format: ranges like <code className="bg-muted px-1 rounded">1-4</code>, individual pages like <code className="bg-muted px-1 rounded">5</code>, or combinations like <code className="bg-muted px-1 rounded">1-3, 5, 8</code>.
                  </p>
                </div>

                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={executeSplit}
                  className="w-full py-3.5 rounded-2xl bg-foreground text-background font-bold text-xs hover:bg-foreground/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-accent" />
                      <span>Extracting pages...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 text-accent" />
                      <span>Extract Pages &amp; Download</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* MODE 3: IMAGES TO PDF                                          */}
        {/* ============================================================== */}
        {mode === "img2pdf" && (
          <div className="space-y-5">
            <div
              onClick={() => imageInputRef.current?.click()}
              className="p-8 rounded-2xl border-2 border-dashed border-border/80 hover:border-accent/50 hover:bg-accent/5 transition-all flex flex-col items-center justify-center text-center gap-3 cursor-pointer group"
            >
              <input
                ref={imageInputRef}
                type="file"
                multiple
                accept="image/png, image/jpeg, image/jpg"
                onChange={handleImagesAdded}
                className="hidden"
              />
              <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent group-hover:scale-105 transition-transform">
                <ImageIcon className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-bold text-foreground">Upload images to convert into a single PDF</p>
                <p className="text-xs text-muted-foreground">Convert photos of homework, chalkboard notes, or handwritten answers</p>
              </div>
            </div>

            {imageFiles.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
                  <span>Selected Images ({imageFiles.length})</span>
                  <button
                    type="button"
                    onClick={() => setImageFiles([])}
                    className="text-red-500 hover:underline cursor-pointer"
                  >
                    Clear All
                  </button>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {imageFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-muted/15 border border-border/60 space-y-1.5 relative group"
                    >
                      <div className="h-20 rounded-lg bg-muted/30 flex items-center justify-center overflow-hidden">
                        <ImageIcon className="w-8 h-8 text-muted-foreground/50" />
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-foreground truncate max-w-[100px]">{file.name}</span>
                        <button
                          type="button"
                          onClick={() => setImageFiles((prev) => prev.filter((_, i) => i !== idx))}
                          className="text-red-500 hover:bg-red-500/10 p-1 rounded cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={executeImagesToPdf}
                  className="w-full py-3.5 rounded-2xl bg-foreground text-background font-bold text-xs hover:bg-foreground/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-accent" />
                      <span>Generating PDF in browser...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 text-accent" />
                      <span>Convert {imageFiles.length} Image(s) to PDF</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
