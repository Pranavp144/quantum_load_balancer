
import streamlit as st
import requests
import plotly.express as px
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Quantum Load Balancer",
    page_icon="⚛️",
    layout="wide"
)

# ---------------- PAGE HEADER ----------------

st.title("⚛️ Quantum Load Balancer")

st.caption(
    "Cost-and-latency-aware scheduling for "
    "classical and simulated quantum workloads."
)

# ---------------- SIDEBAR ----------------

st.sidebar.title("QLB Control Panel")
st.sidebar.subheader("Backend Connection")

try:
    health = requests.get(f"{API_URL}/health", timeout=3)

    if health.status_code == 200:
        st.sidebar.success("Backend Connected")
    else:
        st.sidebar.error("Backend Error")

except requests.RequestException:
    st.sidebar.error("Backend Offline")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Submit Job", "Benchmark"]
)

# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("System Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Scheduling Policies", "3")
    col2.metric("Execution Resources", "2")
    col3.metric("Quantum Simulator", "Qiskit Aer")

    st.markdown("---")

    st.subheader("Scheduling Policies")

    policy_col1, policy_col2, policy_col3 = st.columns(3)

    with policy_col1:
        st.markdown("### Random")
        st.write(
            "Randomly selects between classical "
            "and quantum execution."
        )

    with policy_col2:
        st.markdown("### Greedy")
        st.write(
            "Evaluates estimated execution cost "
            "and latency."
        )

    with policy_col3:
        st.markdown("### Predictive")
        st.write(
            "Considers job deadlines and priority "
            "when selecting a resource."
        )

    st.markdown("---")

    st.subheader("Execution Architecture")

    architecture_col1, architecture_col2 = st.columns(2)

    with architecture_col1:
        st.info(
            "**Classical Executor**\n\n"
            "Simulates classical CPU workload execution."
        )

    with architecture_col2:
        st.info(
            "**Quantum Executor**\n\n"
            "Executes quantum circuits using Qiskit Aer."
        )

    st.warning(
        "Quantum execution uses a local simulator. "
        "No physical quantum computer is connected."
    )


# ==================================================
# SUBMIT JOB
# ==================================================

elif page == "Submit Job":

    st.header("Submit a New Job")

    with st.form("job_form"):

        name = st.text_input(
            "Job Name",
            "My Quantum Job"
        )

        policy = st.selectbox(
            "Scheduling Policy",
            ["random", "greedy", "predictive"],
            index=1
        )

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Classical Configuration")

            classical_runtime = st.number_input(
                "Estimated Classical Runtime (seconds)",
                min_value=0.01,
                value=2.0
            )

            classical_cost = st.number_input(
                "Classical Cost per Second",
                min_value=0.0,
                value=0.02
            )

        with col2:

            st.subheader("Quantum Configuration")

            quantum_runtime = st.number_input(
                "Estimated Quantum Runtime (seconds)",
                min_value=0.01,
                value=1.0
            )

            quantum_cost = st.number_input(
                "Quantum Cost per Second",
                min_value=0.0,
                value=0.15
            )

        priority = st.slider(
            "Job Priority",
            min_value=1,
            max_value=5,
            value=3
        )

        num_qubits = st.number_input(
            "Number of Qubits",
            min_value=1,
            max_value=20,
            value=2
        )

        deadline_enabled = st.checkbox("Set a deadline")

        deadline = None

        if deadline_enabled:

            deadline = st.text_input(
                "Deadline (ISO format)",
                placeholder="2026-10-30T18:00:00"
            )

        submitted = st.form_submit_button(
            "Submit Job",
            use_container_width=True
        )

    # ---------------- JOB EXECUTION ----------------

    if submitted:

        payload = {
            "name": name,
            "classical_runtime": classical_runtime,
            "quantum_runtime": quantum_runtime,
            "classical_cost_per_second": classical_cost,
            "quantum_cost_per_second": quantum_cost,
            "priority": priority,
            "num_qubits": num_qubits,
            "deadline": deadline
        }

        try:

            with st.spinner("Scheduling and executing job..."):

                response = requests.post(
                    f"{API_URL}/jobs/submit",
                    params={"policy": policy},
                    json=payload,
                    timeout=60
                )

            if response.status_code == 200:

                result = response.json()

                job = result["job"]
                metrics = result["metrics"]

                st.success("Job executed successfully!")

                # Execution summary

                st.markdown("---")
                st.subheader("Execution Result")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Execution Target",
                    job["target"].upper()
                )

                col2.metric(
                    "Job Status",
                    job["status"].upper()
                )

                col3.metric(
                    "Actual Runtime",
                    f'{job["actual_runtime"]:.4f} sec'
                    if job.get("actual_runtime") is not None
                    else "N/A"
                )

                # Resource indicator

                if job["target"] == "quantum":
                    st.success("Job assigned to Quantum Executor")
                else:
                    st.info("Job assigned to Classical Executor")

                # Job information

                st.subheader("Job Information")

                info_col1, info_col2, info_col3 = st.columns(3)

                info_col1.metric("Priority", job["priority"])
                info_col2.metric("Qubits", job["num_qubits"])
                info_col3.metric("Job ID", job["job_id"][:8])

                with st.expander("View Complete Job Details"):
                    st.json(job)

                # ---------------- POLICY METRICS ----------------

                st.markdown("---")
                st.subheader("Policy Metrics")

                metric1, metric2, metric3 = st.columns(3)

                metric1.metric(
                    "Total Cost",
                    f'{metrics["total_cost"]:.4f}'
                )

                metric2.metric(
                    "Average Wait Time",
                    f'{metrics["average_wait_time"]:.4f} s'
                )

                metric3.metric(
                    "Turnaround Time",
                    f'{metrics["average_turnaround_time"]:.4f} s'
                )

                # Execution distribution

                st.subheader("Execution Distribution")

                distribution = pd.DataFrame({
                    "Execution Target": [
                        "Classical",
                        "Quantum"
                    ],
                    "Jobs": [
                        metrics["classical_jobs"],
                        metrics["quantum_jobs"]
                    ]
                })

                fig = px.bar(
                    distribution,
                    x="Execution Target",
                    y="Jobs",
                    color="Execution Target",
                    text="Jobs",
                    title="Jobs Executed by Resource"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                # ---------------- QUANTUM RESULTS ----------------

                job_result = job.get("result")

                if job["target"] == "quantum" and job_result:

                    st.markdown("---")
                    st.subheader("Quantum Measurement Results")

                    counts = job_result.get("counts", {})

                    if counts:

                        quantum_data = pd.DataFrame({
                            "Measurement Outcome": list(counts.keys()),
                            "Number of Shots": list(counts.values())
                        })

                        quantum_fig = px.bar(
                            quantum_data,
                            x="Measurement Outcome",
                            y="Number of Shots",
                            text="Number of Shots",
                            title="Quantum Circuit Measurement Distribution"
                        )

                        st.plotly_chart(
                            quantum_fig,
                            use_container_width=True
                        )

                        qcol1, qcol2, qcol3 = st.columns(3)

                        qcol1.metric(
                            "Total Shots",
                            job_result["shots"]
                        )

                        qcol2.metric(
                            "Most Frequent Outcome",
                            job_result["most_frequent_outcome"]
                        )

                        qcol3.metric(
                            "Distinct Outcomes",
                            job_result["distinct_outcomes"]
                        )

                # ---------------- OTHER METRICS ----------------

                st.markdown("---")

                st.subheader("Execution Statistics")

                stat1, stat2, stat3 = st.columns(3)

                stat1.metric(
                    "Failed Jobs",
                    metrics["failed_jobs"]
                )

                stat2.metric(
                    "Deadline Violations",
                    metrics["deadline_violations"]
                )

                stat3.metric(
                    "Total Jobs",
                    metrics["total_jobs"]
                )

            else:

                st.error(
                    f"API Error: {response.status_code}"
                )

                st.write(response.text)

        except requests.RequestException as error:

            st.error(
                f"Could not connect to backend: {error}"
            )


# ==================================================
# BENCHMARK
# ==================================================


# ==================================================
# BENCHMARK
# ==================================================

elif page == "Benchmark":

    st.header("Scheduling Policy Benchmark")

    st.write(
        "Compare Random, Greedy and Predictive scheduling "
        "policies using the same generated workload."
    )

    num_jobs = st.slider(
        "Number of Jobs",
        min_value=1,
        max_value=100,
        value=20
    )

    seed = st.number_input(
        "Random Seed",
        min_value=0,
        value=42
    )

    arrival_mode = st.selectbox(
        "Arrival Mode",
        ["steady", "burst"]
    )

    if st.button("Run Benchmark", use_container_width=True):

        payload = {
            "num_jobs": num_jobs,
            "seed": seed,
            "arrival_mode": arrival_mode
        }

        try:

            with st.spinner("Running benchmark..."):

                response = requests.post(
                    f"{API_URL}/benchmark/run",
                    json=payload,
                    timeout=180
                )

            if response.status_code == 200:

                result = response.json()

                # Correctly access nested benchmark results
                results = result["results"]

                st.success("Benchmark completed successfully!")

                st.markdown("---")

                st.subheader("Benchmark Configuration")
                st.json(result["configuration"])

                # Create comparison table
                benchmark_rows = []

                for policy_name, data in results.items():

                    benchmark_rows.append({
                        "Policy": policy_name.capitalize(),
                        "Total Jobs": data["total_jobs"],
                        "Total Cost": data["total_cost"],
                        "Average Wait Time": data["average_wait_time"],
                        "Average Turnaround": data["average_turnaround_time"],
                        "Deadline Violations": data["deadline_violations"],
                        "Classical Jobs": data["classical_jobs"],
                        "Quantum Jobs": data["quantum_jobs"],
                        "Failed Jobs": data["failed_jobs"],
                        "Wall Clock": data["wall_clock_seconds"]
                    })

                benchmark_df = pd.DataFrame(benchmark_rows)

                st.subheader("Policy Comparison Table")

                st.dataframe(
                    benchmark_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Cost comparison
                st.markdown("---")
                st.subheader("Total Cost Comparison")

                cost_fig = px.bar(
                    benchmark_df,
                    x="Policy",
                    y="Total Cost",
                    color="Policy",
                    text="Total Cost",
                    title="Total Execution Cost by Policy"
                )

                st.plotly_chart(
                    cost_fig,
                    use_container_width=True
                )

                # Wait time comparison
                st.subheader("Average Wait Time Comparison")

                wait_fig = px.bar(
                    benchmark_df,
                    x="Policy",
                    y="Average Wait Time",
                    color="Policy",
                    text="Average Wait Time",
                    title="Average Wait Time by Policy"
                )

                st.plotly_chart(
                    wait_fig,
                    use_container_width=True
                )

                # Turnaround comparison
                st.subheader("Average Turnaround Time Comparison")

                turnaround_fig = px.bar(
                    benchmark_df,
                    x="Policy",
                    y="Average Turnaround",
                    color="Policy",
                    text="Average Turnaround",
                    title="Average Turnaround Time by Policy"
                )

                st.plotly_chart(
                    turnaround_fig,
                    use_container_width=True
                )

                # Resource distribution
                st.subheader("Execution Resource Distribution")

                resource_df = benchmark_df[
                    ["Policy", "Classical Jobs", "Quantum Jobs"]
                ].melt(
                    id_vars="Policy",
                    var_name="Execution Resource",
                    value_name="Number of Jobs"
                )

                resource_fig = px.bar(
                    resource_df,
                    x="Policy",
                    y="Number of Jobs",
                    color="Execution Resource",
                    barmode="group",
                    text="Number of Jobs",
                    title="Classical vs Quantum Jobs by Policy"
                )

                st.plotly_chart(
                    resource_fig,
                    use_container_width=True
                )

                # Raw response
                with st.expander("View Raw Benchmark Response"):
                    st.json(result)

            else:

                st.error(
                    f"Benchmark Error: {response.status_code}"
                )

                st.write(response.text)

        except requests.RequestException as error:

            st.error(
                f"Could not connect to backend: {error}"
            )
