# pybo/views/base_views.py
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count # Count 임포트 추가!
from ..models import Question, Answer


def index(request):
    """
    pybo 목록 출력 (질문 목록 페이징 및 검색)
    """
    # GET 파라미터 가져오기
    page = request.GET.get('page', '1')  # 페이지 번호 (기본값: 1)
    kw = request.GET.get('kw', '')      # 검색어 (기본값: 빈 문자열)
    so = request.GET.get('so', 'recent') # 정렬 기준 (기본값: 'recent')

    # 정렬 기준에 따른 쿼리셋 초기화
    if so == 'popular': # 추천수 정렬
        # 질문에 연결된 답변의 추천수를 모두 합산하여 정렬 (복잡해질 수 있음)
        # 여기서는 질문 자체의 추천수로 정렬하거나, 나중에 추가 구현 필요
        # 현재는 'recommend'가 Answer에 사용되므로 Question에는 일단 최신순으로 둡니다.
        question_list = Question.objects.order_by('-create_date') # 현재 Question 모델에 voter_count가 없으므로 임시
    else: # 'recent' (최신순 정렬)
        question_list = Question.objects.order_by('-create_date')

    # 검색어 처리
    if kw:
        question_list = question_list.filter(
            Q(subject__icontains=kw) |         # 제목 검색
            Q(content__icontains=kw) |         # 내용 검색
            Q(author__username__icontains=kw) | # 질문 글쓴이 검색
            Q(answer__content__icontains=kw) | # 답변 내용 검색
            Q(answer__author__username__icontains=kw) # 답변 글쓴이 검색
        ).distinct() # 중복 제거

    # 페이징 적용
    paginator = Paginator(question_list, 10)  # 페이지당 10개씩 표시
    page_obj = paginator.get_page(page)

    # 템플릿으로 전달할 컨텍스트
    context = {'question_list': page_obj, 'page': page, 'kw': kw, 'so': so}
    return render(request, 'pybo/question_list.html', context)


def detail(request, question_id):
    """
    pybo 질문 상세 출력 (답변 페이징 및 정렬)
    """
    # 질문 객체 가져오기 (없으면 404 에러)
    question = get_object_or_404(Question, pk=question_id)

    # GET 파라미터 가져오기
    page = request.GET.get('page', '1')  # 답변 페이지 번호 (기본값: 1)
    so = request.GET.get('so', 'recent') # 답변 정렬 기준 (기본값: 'recent')

    # 모든 답변에 대해 voter_count를 미리 annotate합니다.
    # Count('voter')는 각 Answer 객체에 연결된 User (voter)의 수를 셉니다.
    answers_qs = Answer.objects.filter(question=question).annotate(
        num_voter=Count('voter')
    )

    # 답변 정렬
    if so == 'recommend':
        # 'num_voter' 필드를 기준으로 내림차순 정렬하고, 같으면 create_date로 정렬
        answer_list = answers_qs.order_by('-num_voter', '-create_date')
    else: # 'recent' (최신순 정렬)
        # 최신순 정렬
        answer_list = answers_qs.order_by('-create_date')

    # 답변 페이징 적용
    paginator = Paginator(answer_list, 5) # 한 페이지에 5개의 답변 표시
    page_obj = paginator.get_page(page)

    # 템플릿으로 전달할 컨텍스트
    context = {'question': question, 'answer_list': page_obj, 'page': page, 'so': so}
    return render(request, 'pybo/question_detail.html', context)