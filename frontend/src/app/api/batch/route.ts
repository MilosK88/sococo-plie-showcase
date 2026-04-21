import { NextResponse } from "next/server";

export async function POST(request: Request) {
  console.log("=== [NEXT.JS] ROUTE HANDLER HIT ===");
  try {
    const targetUrl = `${process.env.BACKEND_URL}/api/generate-batch/1`;
    console.log("=== [NEXT.JS] ATTEMPTING TO FETCH:", targetUrl);
    
    const res = await fetch(targetUrl, {
      method: "POST",
    });

    console.log("=== [FASTAPI] RESPONDED WITH STATUS:", res.status);

    if (res.status === 409) {
      return NextResponse.json(
        { error: "Transaction already in progress. The engine prevents duplicate submissions automatically." },
        { status: 409 }
      );
    }

    if (!res.ok) {
      return NextResponse.json({ error: "Failed to trigger batch" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("=== [NEXT.JS] BATCH ROUTE ERROR:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
