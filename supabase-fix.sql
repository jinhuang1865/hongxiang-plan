-- ============================================================
-- 鸿享计划 浏览量 - Supabase 修复脚本
-- 问题: increment_course_view 函数未设 SECURITY DEFINER,
--       导致 UPSERT 的 UPDATE 路径被 RLS 拦截,浏览量只能+1一次.
-- 修复: 重建函数为 SECURITY DEFINER,以表所有者身份运行,绕过 RLS.
--
-- 执行方式: Supabase Dashboard → SQL Editor → 粘贴本文件内容 → Run
-- ============================================================

-- 1. 重建 increment_course_view 函数 (SECURITY DEFINER)
CREATE OR REPLACE FUNCTION increment_course_view(p_course_id TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE new_count INTEGER;
BEGIN
  INSERT INTO course_views (course_id, views)
  VALUES (p_course_id, 1)
  ON CONFLICT (course_id)
  DO UPDATE SET views = course_views.views + 1
  RETURNING views INTO new_count;
  RETURN new_count;
END;
$$;

-- 2. 授予 anon 角色执行权限
GRANT EXECUTE ON FUNCTION increment_course_view(TEXT) TO anon;

-- 3. 清理旧测试数据 (course-N 格式, 已废弃)
DELETE FROM course_views WHERE course_id LIKE 'course-%';
DELETE FROM course_views WHERE course_id = 'test-url-id-123';

-- 4. 验证: 执行后 course_views 表应为空 (0 行)
SELECT count(*) AS remaining_rows FROM course_views;
