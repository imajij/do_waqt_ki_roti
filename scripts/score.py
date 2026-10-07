#!/usr/bin/env python3
"""Keyword-match score between a job description and a resume.

usage: score.py JD.txt RESUME.json [--master resumes/master/master.json]
prints JSON: {score, jd_keywords, matched, missing, missing_but_in_master, true_gaps}

score = matched / jd_keywords (percent). A keyword counts when any alias appears
(case-insensitive, word-boundary) in the text. 'missing_but_in_master' lists keywords
you could still add truthfully; 'true_gaps' are skills you don't have (never add them).
"""
import json
import re
import sys

# canonical keyword -> aliases (regex fragments)
KEYWORDS = {
    "TypeScript": [r"typescript", r"\bts\b"], "JavaScript": [r"javascript", r"\bjs\b", r"es6"],
    "Python": [r"python"], "Rust": [r"\brust\b"], "Go": [r"\bgolang\b", r"\bgo\b(?=[\s,/)]+(?:lang|developer|services|microservices|,|/|\)))"],
    "Java": [r"\bjava\b(?!script)"], "Kotlin": [r"kotlin"], "Swift": [r"\bswift\b"], "C++": [r"c\+\+"], "C#": [r"c#", r"\.net\b"],
    "Dart": [r"\bdart\b"], "SQL": [r"\bsql\b"], "Bash/Shell": [r"\bbash\b", r"shell scripting"],
    "Node.js": [r"node\.?js", r"\bnode\b"], "Express": [r"express(\.js)?\b"], "NestJS": [r"nest\.?js"], "Fastify": [r"fastify"],
    "React": [r"react(\.js)?\b(?! native)"], "Next.js": [r"next\.?js"], "Vue": [r"vue"], "Angular": [r"angular"],
    "React Native": [r"react native", r"\bexpo\b"], "Flutter": [r"flutter"], "Android": [r"android"], "iOS": [r"\bios\b"],
    "Django": [r"django"], "Flask": [r"flask"], "FastAPI": [r"fastapi"], "Spring Boot": [r"spring"],
    "GraphQL": [r"graphql"], "REST APIs": [r"\brest(ful)?\b", r"\bapis?\b"], "gRPC": [r"grpc"], "tRPC": [r"trpc"],
    "Microservices": [r"micro-?services"], "WebSockets": [r"websockets?"],
    "PostgreSQL": [r"postgres(ql)?"], "MySQL": [r"mysql"], "MongoDB": [r"mongo(db)?"], "Redis": [r"redis"],
    "SQLite": [r"sqlite"], "DynamoDB": [r"dynamodb"], "Elasticsearch": [r"elastic ?search"], "Kafka": [r"kafka"],
    "RabbitMQ": [r"rabbitmq"], "Supabase": [r"supabase"], "Firebase": [r"firebase"], "ORM": [r"\borm\b", r"prisma", r"drizzle", r"sequelize"],
    "AWS": [r"\baws\b", r"amazon web services", r"\bec2\b", r"\bs3\b", r"\becs\b", r"lambda"], "GCP": [r"\bgcp\b", r"google cloud"],
    "Azure": [r"azure"], "Docker": [r"docker", r"container"], "Kubernetes": [r"kubernetes", r"\bk8s\b"],
    "Terraform": [r"terraform"], "CI/CD": [r"ci/?cd", r"continuous (integration|delivery|deployment)", r"github actions", r"jenkins"],
    "GitHub Actions": [r"github actions"], "Linux": [r"linux", r"unix"], "Git": [r"\bgit\b", r"github", r"gitlab"],
    "Nginx": [r"nginx"], "Cloudflare": [r"cloudflare"], "Serverless": [r"serverless"], "Monitoring/Observability": [r"monitoring", r"observability", r"prometheus", r"grafana", r"datadog"],
    "Infrastructure as Code": [r"infrastructure as code", r"\biac\b"], "Networking": [r"networking", r"tcp/ip", r"\bdns\b"],
    "Testing": [r"unit test", r"testing", r"pytest", r"jest", r"\btests?\b"], "System Design": [r"system design", r"distributed systems?", r"scalab"],
    "Data Structures & Algorithms": [r"data structures", r"algorithms", r"\bdsa\b"], "OOP": [r"object[- ]oriented", r"\boop\b"],
    "LLMs/GenAI": [r"\bllms?\b", r"generative ai", r"\bgenai\b", r"openai", r"gpt", r"large language model", r"\bagents?\b", r"\brag\b"],
    "Machine Learning": [r"machine learning", r"\bml\b", r"pytorch", r"tensorflow"], "Automation": [r"automat"],
    "Open Source": [r"open[- ]source"], "Customer-facing": [r"customer", r"client"], "Debugging": [r"debug", r"troubleshoot"],
    "Performance": [r"performance", r"latency", r"optimi[sz]"], "Security": [r"security", r"auth(entication|orization)", r"\brbac\b", r"oauth"],
    "Multi-tenancy": [r"multi-?tenan"], "HTML/CSS": [r"\bhtml", r"\bcss\b", r"tailwind"], "Agile": [r"agile", r"scrum"],
}


def present(text, aliases):
    return any(re.search(a, text, re.I) for a in aliases)


def resume_text(obj):
    if isinstance(obj, dict):
        return " ".join(resume_text(v) for k, v in obj.items() if not k.startswith("_") and not k.endswith("_note"))
    if isinstance(obj, list):
        return " ".join(resume_text(v) for v in obj)
    return str(obj)


def main():
    args = sys.argv[1:]
    master_path = None
    if "--master" in args:
        i = args.index("--master")
        master_path = args[i + 1]
        del args[i:i + 2]
    jd = open(args[0]).read()
    res = resume_text(json.load(open(args[1])))
    master = resume_text(json.load(open(master_path))) if master_path else ""
    jd_kw = [k for k, a in KEYWORDS.items() if present(jd, a)]
    matched = [k for k in jd_kw if present(res, KEYWORDS[k])]
    missing = [k for k in jd_kw if k not in matched]
    in_master = [k for k in missing if master and present(master, KEYWORDS[k])]
    gaps = [k for k in missing if k not in in_master]
    score = round(100 * len(matched) / len(jd_kw)) if jd_kw else 0
    print(json.dumps({"score": score, "jd_keywords": jd_kw, "matched": matched, "missing": missing,
                      "missing_but_in_master": in_master, "true_gaps": gaps}, indent=1))


if __name__ == "__main__":
    main()
