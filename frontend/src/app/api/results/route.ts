import { NextResponse } from "next/server";

export async function GET(request: Request) {
  try {
    const backendUrl = `${process.env.BACKEND_URL}/api/results/1`;
    
    const res = await fetch(backendUrl, {
      method: "GET",
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Failed to fetch results" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
