insert into storage.buckets (id, name)
values ('scans', 'scans');

create policy "Scans images are publicly accessible."
  on storage.objects for select
  using ( bucket_id = 'scans' );

create policy "Anyone can upload a scans."
  on storage.objects for insert
  with check ( bucket_id = 'scans' );

create policy "Anyone can update a scans."
  on storage.objects for update
  with check ( bucket_id = 'scans' );
