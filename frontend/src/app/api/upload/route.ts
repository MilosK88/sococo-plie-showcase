import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const backendUrl = `${process.env.BACKEND_URL}/api/upload-csv/1`;
    
    const res = await fetch(backendUrl, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Failed to upload to backend" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
