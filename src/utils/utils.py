
def flatten_jobs_array(nested_job_data):
    flattened_jobs = []

    for job_group in nested_job_data:
        if job_group is None:
            flattened_jobs.append([None, None, None, None])
            continue

        for job_entry in job_group:
            if job_entry is None:
                flattened_jobs.append([None, None, None, None])
                continue

            job_details = []

            for field in job_entry:
                job_details.append(field)

            flattened_jobs.append(job_details)

    return flattened_jobs
