import fs from 'fs';
import path from 'path';

export default function handler(req: any, res: { setHeader: (arg0: string, arg1: string) => void; end: (arg0: Buffer) => void; }) {
    const imagePath = path.join(process.cwd(), 'public', 'logo.png');
    const image = fs.readFileSync(imagePath);
    res.setHeader('Content-Type', 'image/png');
    res.end(image);
}