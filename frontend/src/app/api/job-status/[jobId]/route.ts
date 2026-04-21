import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const resolvedParams = await params;
    const jobId = resolvedParams.jobId;

    const backendUrl = `${process.env.BACKEND_URL}/api/job-status/${jobId}`;
    
    const res = await fetch(backendUrl, {
      method: "GET",
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Failed to fetch job status" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
