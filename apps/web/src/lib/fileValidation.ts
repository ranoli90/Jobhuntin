/**
 * D1: Validate file type by magic bytes (not just MIME from OS).
 * PDF: %PDF (25 50 44 46)
 * DOCX: PK.. (50 4B 03 04) - ZIP format
 */
const PDF_MAGIC = new Uint8Array([0x25, 0x50, 0x44, 0x46]);
const ZIP_MAGIC = new Uint8Array([0x50, 0x4b, 0x03, 0x04]);
const ZIP_MAGIC_ALT = new Uint8Array([0x50, 0x4b, 0x05, 0x06]);

function matchesMagic(file: File, magic: Uint8Array): Promise<boolean> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => {
      const arr = new Uint8Array(reader.result as ArrayBuffer);
      const match = arr.length >= magic.length && magic.every((b, i) => arr[i] === b);
      resolve(match);
    };
    reader.onerror = () => resolve(false);
    reader.readAsArrayBuffer(file.slice(0, Math.max(magic.length, 4)));
  });
}

export async function isValidResumeFile(file: File): Promise<{ valid: boolean; reason?: string }> {
  if (file.type === "application/pdf") {
    const isPdf = await matchesMagic(file, PDF_MAGIC);
    if (!isPdf) return { valid: false, reason: "File may be corrupted or not a valid PDF" };
    return { valid: true };
  }
  if (file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
    const isZip = await matchesMagic(file, ZIP_MAGIC) || (await matchesMagic(file, ZIP_MAGIC_ALT));
    if (!isZip) return { valid: false, reason: "File may be corrupted or not a valid Word document" };
    return { valid: true };
  }
  if (file.type === "application/msword") return { valid: true }; // .doc - trust type
  return { valid: false, reason: "Please upload a PDF or Word document" };
}
