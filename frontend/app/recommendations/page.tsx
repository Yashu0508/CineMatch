"use client";
import Link from "next/link";
import { PageHeading, PageShell } from "@/components/common/page-shell";
import { EmptyState, ErrorState, SkeletonGrid } from "@/components/common/states";
import { MovieGrid } from "@/components/movies/movie-rail";
import { useRecommendations } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth/context";
import { useRouter } from "next/navigation";
export default function RecommendationsPage(){const {user}=useAuth();const router=useRouter();const recs=useRecommendations();if(!user)return <PageShell><EmptyState title="Sign in to unlock recommendations" action={<button onClick={()=>router.push('/login')} className="rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Sign in</button>}/></PageShell>;return <PageShell><PageHeading eyebrow="Made for you" title="Your movie compass" description="Recommendations shaped by your preferences and the signals you leave behind." />{recs.isLoading?<SkeletonGrid count={12}/>:recs.isError?<ErrorState message="Personalized recommendations are not available right now."/>:recs.data.length?<><MovieGrid movies={recs.data}/><p className="mt-12 text-center text-sm text-white/40">Rate or watch more films to keep tuning your compass.</p></>:<EmptyState title="Rate a few movies to improve your recommendations" action={<Link href="/movies" className="inline-block rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Browse movies</Link>}/>}</PageShell>}
