import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Define the shape of a message
interface FeedbackMessage {
    id: string;
    name: string;
    content: string;
    timestamp: string;
}

// Path to our local JSON file
const dataFilePath = path.join(process.cwd(), 'data', 'feedback.json');

// Helper to ensure the file exists
const ensureDataFileExists = () => {
    const dirPath = path.dirname(dataFilePath);
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
    if (!fs.existsSync(dataFilePath)) {
        fs.writeFileSync(dataFilePath, JSON.stringify([]), 'utf-8');
    }
};

export async function GET() {
    try {
        ensureDataFileExists();
        const fileContents = fs.readFileSync(dataFilePath, 'utf-8');
        const messages: FeedbackMessage[] = JSON.parse(fileContents);
        return NextResponse.json(messages);
    } catch (error) {
        console.error('Error reading feedback API:', error);
        return NextResponse.json({ error: 'Failed to read messages' }, { status: 500 });
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { name, content } = body;

        if (!name || !content || name.trim() === '' || content.trim() === '') {
            return NextResponse.json({ error: 'Name and content are required' }, { status: 400 });
        }

        ensureDataFileExists();
        const fileContents = fs.readFileSync(dataFilePath, 'utf-8');
        const messages: FeedbackMessage[] = JSON.parse(fileContents);

        const newMessage: FeedbackMessage = {
            id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
            name: name.trim().substring(0, 50), // Limit name size
            content: content.trim().substring(0, 500), // Limit content size
            timestamp: new Date().toISOString(),
        };

        // Keep only the latest 100 messages to prevent infinite file growth
        const updatedMessages = [newMessage, ...messages].slice(0, 100);

        fs.writeFileSync(dataFilePath, JSON.stringify(updatedMessages, null, 2), 'utf-8');

        return NextResponse.json(newMessage, { status: 201 });
    } catch (error) {
        console.error('Error writing feedback API:', error);
        return NextResponse.json({ error: 'Failed to post message' }, { status: 500 });
    }
}
